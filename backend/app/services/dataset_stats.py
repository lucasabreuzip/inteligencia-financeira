from __future__ import annotations

from psycopg.rows import dict_row

from app.infrastructure.db import sync_connection


    # Snapshot compacto para injetar como contexto global no prompt RAG
def fetch_dataset_snapshot(job_id: str) -> dict:
    
    with sync_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:

            cur.execute(
                "SELECT * FROM kpis WHERE job_id = %s", (job_id,)
            )
            kpi = cur.fetchone()

            cur.execute(
                """
                SELECT status, COUNT(*) AS qtd, ROUND(SUM(valor)::numeric, 2) AS soma
                FROM transactions
                WHERE job_id = %s
                GROUP BY status
                ORDER BY qtd DESC
                """,
                (job_id,),
            )
            status_rows = cur.fetchall()

            cur.execute(
                """
                SELECT cliente, COUNT(*) AS qtd, ROUND(SUM(valor)::numeric, 2) AS soma
                FROM transactions
                WHERE job_id = %s
                GROUP BY cliente
                ORDER BY soma DESC
                LIMIT 10
                """,
                (job_id,),
            )
            clientes_rows = cur.fetchall()

            cur.execute(
                "SELECT COUNT(*) as c FROM transactions WHERE job_id = %s", (job_id,)
            )
            total = cur.fetchone()["c"]

    return {
        "total_transacoes_base": int(total) if total else 0,
        "receita_total": kpi["receita_total"] if kpi else None,
        "ticket_medio": kpi["ticket_medio"] if kpi else None,
        "taxa_inadimplencia": kpi["taxa_inadimplencia"] if kpi else None,
        "periodo": {
            "inicio": kpi["periodo_inicio"] if kpi else None,
            "fim": kpi["periodo_fim"] if kpi else None,
        },
        "por_status": [
            {"status": r["status"], "qtd": r["qtd"], "soma": float(r["soma"])}
            for r in status_rows
        ],
        "top_clientes": [
            {"cliente": r["cliente"], "qtd": r["qtd"], "soma": float(r["soma"])}
            for r in clientes_rows
        ],
    }


def format_snapshot_for_prompt(snap: dict) -> str:
    status_str = ", ".join(
        f"{s['status']}={s['qtd']} (R$ {s['soma']:.2f})" for s in snap["por_status"]
    )
    top_str = "; ".join(
        f"{c['cliente']}: R$ {c['soma']:.2f} ({c['qtd']})" for c in snap["top_clientes"]
    )
    periodo = snap["periodo"]
    return (
        f"[ESTATÍSTICAS GLOBAIS DA BASE — use para perguntas de contagem/totais]\n"
        f"- Total de transações na base: {snap['total_transacoes_base']}\n"
        f"- Período: {periodo['inicio']} x {periodo['fim']}\n"
        f"- Receita total (pago): R$ {snap['receita_total']:.2f}\n"
        f"- Ticket médio: R$ {snap['ticket_medio']:.2f}\n"
        f"- Taxa de inadimplência: {snap['taxa_inadimplencia']*100:.2f}%\n"
        f"- Distribuição por status: {status_str}\n"
        f"- Top 10 clientes por valor: {top_str}"
    )
