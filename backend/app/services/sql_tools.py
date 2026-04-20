from __future__ import annotations

from psycopg.rows import dict_row
from typing import Any, Literal

from app.infrastructure.db import sync_connection

ALLOWED_ORDER_COLUMNS = {"data", "valor", "cliente", "status"}
ALLOWED_ORDER_DIR = {"asc", "desc"}
ALLOWED_GROUP_BY = {"status", "cliente", "mes"}
ALLOWED_METRICS = {"count", "sum", "avg"}


def _base_where(job_id: str, filters: dict[str, Any]) -> tuple[str, list]:
    clauses = ["job_id = %s"]
    params: list = [job_id]

    if filters.get("id"):
        clauses.append("id = %s")
        params.append(str(filters["id"]))
    if filters.get("status"):
        clauses.append("LOWER(status) = %s")
        params.append(str(filters["status"]).lower())
    if filters.get("categoria"):
        clauses.append("LOWER(categoria) = %s")
        params.append(str(filters["categoria"]).lower())
    if filters.get("cliente_contains"):
        clauses.append("LOWER(cliente) LIKE %s")
        params.append(f"%{str(filters['cliente_contains']).lower()}%")
    if filters.get("descricao_contains"):
        clauses.append("LOWER(descricao) LIKE %s")
        params.append(f"%{str(filters['descricao_contains']).lower()}%")
    if filters.get("min_valor") is not None:
        clauses.append("valor >= %s")
        params.append(float(filters["min_valor"]))
    if filters.get("max_valor") is not None:
        clauses.append("valor <= %s")
        params.append(float(filters["max_valor"]))
    # Cast explicito para DATE: evita ambiguidade de tipo quando o parametro
    # chega como string ISO. Postgres resolve "YYYY-MM-DD" -> DATE sem problema.
    if filters.get("data_inicio"):
        clauses.append("data >= %s::date")
        params.append(str(filters["data_inicio"]))
    if filters.get("data_fim"):
        clauses.append("data <= %s::date")
        params.append(str(filters["data_fim"]))

    return " AND ".join(clauses), params


def list_transactions(
    job_id: str,
    filters: dict[str, Any] | None = None,
    order_by: str = "data",
    order_dir: str = "desc",
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    filters = filters or {}
    if order_by not in ALLOWED_ORDER_COLUMNS:
        order_by = "data"
    if order_dir.lower() not in ALLOWED_ORDER_DIR:
        order_dir = "desc"
    limit = max(1, min(int(limit), 200))
    offset = max(0, int(offset))

    where, params = _base_where(job_id, filters)
    sql = (
        f"SELECT id, valor, TO_CHAR(data, 'YYYY-MM-DD') AS data, "
        f"status, cliente, descricao, categoria "
        f"FROM transactions WHERE {where} "
        f"ORDER BY {order_by} {order_dir.upper()} LIMIT %s OFFSET %s"
    )
    params.extend([limit, offset])

    with sync_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def count_transactions(
    job_id: str, filters: dict[str, Any] | None = None
) -> dict:
    filters = filters or {}
    where, params = _base_where(job_id, filters)
    sql = (
        f"SELECT COUNT(*) AS qtd, "
        f"ROUND(COALESCE(SUM(valor)::numeric, 0), 2) AS soma, "
        f"ROUND(COALESCE(AVG(valor)::numeric, 0), 2) AS media "
        f"FROM transactions WHERE {where}"
    )
    with sync_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
    return {"qtd": int(row["qtd"]), "soma": float(row["soma"]), "media": float(row["media"])}


def aggregate_transactions(
    job_id: str,
    group_by: Literal["status", "cliente", "mes"],
    metric: Literal["count", "sum", "avg"],
    filters: dict[str, Any] | None = None,
    limit: int = 20,
) -> list[dict]:
    if group_by not in ALLOWED_GROUP_BY:
        raise ValueError(f"group_by inválido: {group_by}")
    if metric not in ALLOWED_METRICS:
        raise ValueError(f"metric inválido: {metric}")

    filters = filters or {}
    where, params = _base_where(job_id, filters)
    limit = max(1, min(int(limit), 100))

    group_expr = {
        "status": "status",
        "cliente": "cliente",
        "mes": "TO_CHAR(data, 'YYYY-MM')",
    }[group_by]

    metric_expr = {
        "count": "COUNT(*)",
        "sum": "ROUND(SUM(valor)::numeric, 2)",
        "avg": "ROUND(AVG(valor)::numeric, 2)",
    }[metric]

    sql = (
        f"SELECT {group_expr} AS grupo, {metric_expr} AS valor_metrica, "
        f"COUNT(*) AS qtd "
        f"FROM transactions WHERE {where} "
        f"GROUP BY {group_expr} ORDER BY valor_metrica DESC LIMIT %s"
    )
    params.append(limit)

    with sync_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

    return [
        {"grupo": r["grupo"], "valor_metrica": float(r["valor_metrica"]), "qtd": int(r["qtd"])}
        for r in rows
    ]


def semantic_search_db(
    job_id: str,
    query_vector: list[float],
    k: int = 20,
    categoria: str | None = None,
    relevance_threshold: float = 1.6,
) -> tuple[list[dict], str]:
    """Execute similar search directly in postgres via pgvector `<=>`."""
    base_where_parts = ["job_id = %s", "embedding IS NOT NULL"]
    params = [job_id]

    if categoria:
        base_where_parts.append("LOWER(categoria) = %s")
        params.append(categoria.lower())

    vec_str = str(query_vector)

    where_clause = " AND ".join(base_where_parts)

    sql = f"""
        SELECT
            id, valor, TO_CHAR(data, 'YYYY-MM-DD') AS data,
            status, cliente, descricao, categoria,
            (embedding <=> %s) AS distance_score
        FROM transactions
        WHERE {where_clause}
        ORDER BY distance_score ASC
        LIMIT %s
    """

    # Parâmetros na exata ordem do SQL (SELECT, WHERE, LIMIT)
    sql_params = [vec_str] + params + [k]

    with sync_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, sql_params)
            rows = cur.fetchall()

    filtered = []
    for r in rows:
        score = r["distance_score"]
        if score > relevance_threshold:
            continue
        filtered.append(r)

    quality = "ótima" if filtered and filtered[0]["distance_score"] < 0.5 else "boa" if filtered and filtered[0]["distance_score"] < 0.9 else "fraca" if filtered else "nenhuma"

    return filtered, quality
