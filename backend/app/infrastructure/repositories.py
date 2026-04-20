"""
Repositório de jobs e KPIs.

CRUD para as tabelas `jobs`, `kpis` e `timeseries`, além de queries
compostas como `fetch_dashboard` que juntam múltiplas tabelas.
"""
from __future__ import annotations

import json

import psycopg
from psycopg.rows import dict_row

from .pool import async_connection, sync_connection


def upsert_job(conn: psycopg.Connection, job_id: str, filename: str, status: str, error: str | None = None) -> None:
    conn.execute(
        """
        INSERT INTO jobs (job_id, filename, status, error)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(job_id) DO UPDATE SET
            status = EXCLUDED.status,
            error = EXCLUDED.error,
            updated_at = NOW()
        """,
        (job_id, filename, status, error),
    )


def save_kpis(
    conn: psycopg.Connection,
    job_id: str,
    kpis: dict,
    insights_json: str | None,
) -> None:
    conn.execute(
        """
        INSERT INTO kpis (
            job_id, total_transacoes, receita_total, ticket_medio,
            taxa_inadimplencia, inadimplencia_valor, periodo_inicio,
            periodo_fim, ai_insights_json
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT(job_id) DO UPDATE SET
            total_transacoes=EXCLUDED.total_transacoes,
            receita_total=EXCLUDED.receita_total,
            ticket_medio=EXCLUDED.ticket_medio,
            taxa_inadimplencia=EXCLUDED.taxa_inadimplencia,
            inadimplencia_valor=EXCLUDED.inadimplencia_valor,
            periodo_inicio=EXCLUDED.periodo_inicio,
            periodo_fim=EXCLUDED.periodo_fim,
            ai_insights_json=EXCLUDED.ai_insights_json
        """,
        (
            job_id,
            kpis["total_transacoes"],
            kpis["receita_total"],
            kpis["ticket_medio"],
            kpis["taxa_inadimplencia"],
            kpis["inadimplencia_valor"],
            kpis["periodo_inicio"],
            kpis["periodo_fim"],
            insights_json,
        ),
    )


def save_timeseries(conn: psycopg.Connection, job_id: str, rows: list[tuple[str, float, int]]) -> None:
    conn.execute("DELETE FROM timeseries WHERE job_id = %s", (job_id,))
    if not rows:
        return
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO timeseries (job_id, periodo, receita, transacoes) VALUES (%s, %s, %s, %s)",
            [(job_id, p, r, t) for p, r, t in rows],
        )

 #Usa COPY ordem de magnitude mais rápido que executemany para milhares de linhas.
def save_transactions(conn: psycopg.Connection, job_id: str, rows: list[tuple]) -> None:
    conn.execute("DELETE FROM transactions WHERE job_id = %s", (job_id,))
    if not rows:
        return
    copy_sql = (
        "COPY transactions "
        "(id, job_id, valor, data, status, cliente, descricao, categoria) "
        "FROM STDIN"
    )
    with conn.cursor() as cur:
        with cur.copy(copy_sql) as cp:
            for row in rows:
                cp.write_row(row)


async def fetch_job_status(job_id: str) -> dict | None:
    async with async_connection() as aconn:
        async with aconn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT job_id, filename, status, error, updated_at FROM jobs WHERE job_id = %s",
                (job_id,),
            )
            return await cur.fetchone()


async def fetch_dashboard(job_id: str) -> dict | None:
    async with async_connection() as aconn:
        async with aconn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                SELECT k.*, j.filename
                FROM kpis k
                JOIN jobs j ON k.job_id = j.job_id
                WHERE k.job_id = %s
                """,
                (job_id,),
            )
            kpi_row = await cur.fetchone()

            if kpi_row is None:
                return None

            await cur.execute(
                "SELECT periodo, receita, transacoes FROM timeseries WHERE job_id = %s ORDER BY periodo",
                (job_id,),
            )
            ts_rows = await cur.fetchall()

    insights = None
    if kpi_row["ai_insights_json"]:
        insights = json.loads(kpi_row["ai_insights_json"])

    return {
        "job_id": job_id,
        "filename": kpi_row["filename"],
        "total_transacoes": kpi_row["total_transacoes"],
        "receita_total": kpi_row["receita_total"],
        "ticket_medio": kpi_row["ticket_medio"],
        "taxa_inadimplencia": kpi_row["taxa_inadimplencia"],
        "inadimplencia_valor": kpi_row["inadimplencia_valor"],
        "periodo_inicio": kpi_row["periodo_inicio"],
        "periodo_fim": kpi_row["periodo_fim"],
        "insights": insights,
        "timeseries": [
            {"periodo": r["periodo"], "receita": r["receita"], "transacoes": r["transacoes"]}
            for r in ts_rows
        ],
    }

    # Retorna o JSON de insights salvo em kpis.ai_insights_json
def fetch_ai_insights_json(job_id: str) -> str | None:
    with sync_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT ai_insights_json FROM kpis WHERE job_id = %s", (job_id,))
            row = cur.fetchone()
    return row[0] if row and row[0] else None


async def fetch_latest_job() -> str | None:
    async with async_connection() as aconn:
        async with aconn.cursor() as cur:
            await cur.execute(
                "SELECT job_id FROM jobs WHERE status = 'done' ORDER BY updated_at DESC LIMIT 1"
            )
            row = await cur.fetchone()
    return row[0] if row else None
