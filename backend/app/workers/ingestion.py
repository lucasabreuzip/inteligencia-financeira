from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.core.config import get_settings
from app.infrastructure.db import save_kpis, save_timeseries, save_transactions, sync_connection, upsert_job
from app.infrastructure.job_store import job_store
from app.services.analytics import build_llm_summary, compute_kpis, compute_monthly_timeseries
from app.services.etl import ETLError, load_and_clean_csv
from app.services.llm_insights import generate_insights
from app.services.rag_indexer import build_vector_index

logger = logging.getLogger(__name__)

# Concorrência máxima de pipelines pesados rodando ao mesmo tempo.
# Evita saturar CPU / rate limit da OpenAI / pool de conexões quando
# múltiplos usuários sobem CSV em paralelo. Jobs além do limite ficam
# em fila (status permanece "queued" até que um slot libere).
# Configurável via MAX_CONCURRENT_PIPELINES no .env.
_pipeline_semaphore = asyncio.Semaphore(get_settings().max_concurrent_pipelines)


async def _publish(job_id: str, status, progress: int, message: str) -> None:
    await job_store.publish(job_id, status, progress, message)


def _persist_everything(
    job_id: str, filename: str, df, kpis: dict, timeseries, insights_json: str | None
) -> None:
    tx_rows = [
        (
            row.id,
            job_id,
            float(row.valor),
            # Pandas Timestamp -> datetime.date: psycopg3 serializa nativamente
            # para DATE via COPY sem strftime. Alinha com o novo schema.
            row.data.date() if hasattr(row.data, "date") else row.data,
            row.status,
            row.cliente,
            row.descricao,
            row.categoria,
        )
        for row in df.itertuples(index=False)
    ]
    with sync_connection() as conn:
        with conn.transaction():
            upsert_job(conn, job_id, filename=filename, status="persisting")
            save_transactions(conn, job_id, tx_rows)
            save_kpis(conn, job_id, kpis, insights_json)
            save_timeseries(conn, job_id, timeseries)


async def run_ingestion_pipeline(job_id: str, file_path: Path) -> None:
    # Mostra status "queued" enquanto espera um slot — UX consistente
    # quando há fila de uploads simultâneos.
    async with _pipeline_semaphore:
        await _run_pipeline(job_id, file_path)


async def _run_pipeline(job_id: str, file_path: Path) -> None:
    # Recupera metadados iniciais para evitar multiplas chamadas async ao store
    state = await job_store.get(job_id)
    if not state:
        logger.error("Job %s não encontrado no store ao iniciar pipeline.", job_id)
        return
    filename = state.filename

    try:
        await _publish(job_id, "reading", 10, "Lendo arquivo")
        df = await asyncio.to_thread(load_and_clean_csv, file_path)

        await _publish(job_id, "cleaning", 30, f"{len(df)} linhas higienizadas")
        await _publish(job_id, "computing", 50, "Calculando KPIs e série temporal")

        kpis = await asyncio.to_thread(compute_kpis, df)
        timeseries = await asyncio.to_thread(compute_monthly_timeseries, df)
        summary = await asyncio.to_thread(build_llm_summary, df, kpis, timeseries)

        await _publish(job_id, "ai", 70, "Gerando classificação e alertas via LLM")
        insights = await asyncio.to_thread(generate_insights, summary)
        insights_json = insights.model_dump_json() if insights else None

        await _publish(job_id, "persisting", 80, "Gravando dados padronizados no PostgreSQL")
        await asyncio.to_thread(_persist_everything, job_id, filename, df, kpis, timeseries, insights_json)

        await _publish(job_id, "embedding", 90, "Indexando transações no PGVector para RAG")
        rag_note = ""
        try:
            async def report_progress(msg: str):
                await _publish(job_id, "embedding", 90, msg)

            indexed = await build_vector_index(job_id, on_progress=report_progress)
            logger.info("Job %s: %d documentos indexados", job_id, indexed)
            if indexed == 0:
                rag_note = " (RAG desabilitado: sem OPENAI_API_KEY)"
        except Exception as exc:
            logger.warning("Indexação RAG falhou para job=%s: %s", job_id, exc)
            rag_note = f" (RAG indisponível: {type(exc).__name__})"

        with sync_connection() as conn:
            upsert_job(conn, job_id, filename=filename, status="done")

        await _publish(job_id, "done", 100, "Processamento concluído" + rag_note)
    except ETLError as exc:
        logger.warning("ETLError job=%s: %s", job_id, exc)
        with sync_connection() as conn:
            upsert_job(
                conn, job_id, filename=filename,
                status="failed", error=str(exc),
            )
        await job_store.publish(job_id, "failed", 100, f"Erro de validação: {exc}", error=str(exc))
    except Exception as exc:
        logger.exception("Falha inesperada job=%s", job_id)
        with sync_connection() as conn:
            upsert_job(
                conn, job_id, filename=filename,
                status="failed", error=str(exc),
            )
        await job_store.publish(job_id, "failed", 100, "Erro interno no processamento", error=str(exc))
