from __future__ import annotations

import asyncio
import logging
from typing import Any
from collections.abc import Callable

from psycopg.rows import dict_row

from app.core.config import get_settings
from app.infrastructure.db import async_connection
from app.services.embedding_client import get_embedding_client
from app.services.observability import observe

logger = logging.getLogger(__name__)

# Quantas linhas por UPDATE ... FROM (VALUES ...). 500 equilibra latencia por
# roundtrip, memoria e tamanho do packet de rede enviado ao Postgres.
DB_UPDATE_BATCH_SIZE = 500


def _build_document(row: dict) -> str:
    """
    Texto a ser embeddado. Decisao de design: incluimos APENAS campos com
    conteudo semantico (categoria + descricao). Campos estruturais (id, valor,
    data, status, cliente) poluem o espaco vetorial — eles ja sao filtraveis
    via SQL. Remove-los melhora precision@k em queries qualitativas.
    """
    categoria = (row.get("categoria") or "outros").strip()
    descricao = (row.get("descricao") or "").strip()
    return f"[{categoria}] {descricao}" if descricao else f"[{categoria}]"


async def _load_transactions(job_id: str, limit: int = 1000) -> list[dict]:
    async with async_connection() as aconn:
        async with aconn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT id, descricao, categoria
                FROM transactions
                WHERE job_id = %s AND embedding IS NULL
                ORDER BY id
                LIMIT %s
                """,
                (job_id, limit),
            )
            return await cur.fetchall()


async def _persist_embeddings(
    job_id: str, rows: list[dict], vectors: list[list[float]]
) -> None:

    async with async_connection() as aconn:
        async with aconn.cursor() as cur:
            for start in range(0, len(rows), DB_UPDATE_BATCH_SIZE):
                chunk_rows = rows[start : start + DB_UPDATE_BATCH_SIZE]
                chunk_vecs = vectors[start : start + DB_UPDATE_BATCH_SIZE]

                values_sql = ",".join(["(%s::vector, %s, %s)"] * len(chunk_rows))
                sql = (
                    f"UPDATE transactions AS t SET embedding = v.emb "
                    f"FROM (VALUES {values_sql}) AS v(emb, id, job_id) "
                    f"WHERE t.id = v.id AND t.job_id = v.job_id"
                )
                params: list = []
                for row, vec in zip(chunk_rows, chunk_vecs):
                    params.extend([str(vec), row["id"], job_id])
                await cur.execute(sql, params)
            await aconn.commit()


async def _count_remaining(job_id: str) -> int:
    async with async_connection() as aconn:
        async with aconn.cursor() as cur:
            await cur.execute(
                "SELECT COUNT(*) FROM transactions WHERE job_id = %s AND embedding IS NULL",
                (job_id,),
            )
            row = await cur.fetchone()
            return row[0] if row else 0

 #Gera embeddings em lotes paralelos com feedback visual de progresso (X/Y)
@observe(name="rag_indexation")
async def build_vector_index(job_id: str, on_progress: Callable[[str], Any] | None = None) -> int:
    settings = get_settings()
    if not settings.openai_api_key:
        logger.warning("OPENAI_API_KEY ausente - pulando indexacao vetorial.")
        return 0

    total_to_process = await _count_remaining(job_id)
    if total_to_process == 0:
        return 0

    # Lotes menores para economizar memoria e CPU no parse de strings
    BATCH_SIZE = 400
    # Processamos ate 3 lotes simultaneamente (balanceado para 2vCPU)
    CONCURRENCY = 3
    semaphore = asyncio.Semaphore(CONCURRENCY)
    total_indexed = 0

    async def _process_batch(rows: list[dict]):
        nonlocal total_indexed
        async with semaphore:
            docs = [_build_document(r) for r in rows]
            client = get_embedding_client()
            vectors = await client.aembed_documents(docs)
            await _persist_embeddings(job_id, rows, vectors)
            total_indexed += len(rows)
            if on_progress:
                await on_progress(f"Treinando sua IA (Indexando RAG): {total_indexed} / {total_to_process}...")

    while True:
        # Carregamos uma "janela" de trabalho para disparar tasks
        work_batch = await _load_transactions(job_id, limit=BATCH_SIZE * CONCURRENCY)
        if not work_batch:
            break

        tasks = []
        for i in range(0, len(work_batch), BATCH_SIZE):
            chunk = work_batch[i : i + BATCH_SIZE]
            tasks.append(_process_batch(chunk))

        await asyncio.gather(*tasks)
        # Yield explícito para o event loop respirar (atende status poll do front)
        await asyncio.sleep(0)

    if total_indexed > 0:
        logger.info("Fim da indexacao PgVector: job=%s total=%d docs", job_id, total_indexed)

    return total_indexed
