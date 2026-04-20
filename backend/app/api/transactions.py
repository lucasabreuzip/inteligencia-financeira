import asyncio
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import require_api_key
from app.domain.schemas import TransactionItem, TransactionsPageResponse
from app.services.categorizer import CATEGORY_LABELS
from app.services.sql_tools import ALLOWED_ORDER_COLUMNS, ALLOWED_ORDER_DIR, count_transactions, list_transactions

router = APIRouter(prefix="/api", tags=["transactions"], dependencies=[Depends(require_api_key)])


@router.get("/transactions/{job_id}", response_model=TransactionsPageResponse)
async def get_transactions(
    job_id: str,
    status: str | None = Query(None),
    categoria: str | None = Query(None),
    cliente_contains: str | None = Query(None),
    min_valor: float | None = Query(None),
    max_valor: float | None = Query(None),
    data_inicio: str | None = Query(None),
    data_fim: str | None = Query(None),
    order_by: Literal["data", "valor", "cliente", "status"] = "data",
    order_dir: Literal["asc", "desc"] = "desc",
    offset: int = Query(0, ge=0),
    limit: int = Query(15, ge=1, le=200),
) -> TransactionsPageResponse:
    if order_by not in ALLOWED_ORDER_COLUMNS:
        raise HTTPException(400, "order_by inválido")
    if order_dir not in ALLOWED_ORDER_DIR:
        raise HTTPException(400, "order_dir inválido")

    filters: dict = {
        "status": status,
        "categoria": categoria,
        "cliente_contains": cliente_contains,
        "min_valor": min_valor,
        "max_valor": max_valor,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    }
    filters = {k: v for k, v in filters.items() if v not in (None, "")}

    total_info = await asyncio.to_thread(count_transactions, job_id, filters)
    rows = await asyncio.to_thread(
        list_transactions,
        job_id,
        filters,
        order_by,
        order_dir,
        limit,
        offset,
    )

    return TransactionsPageResponse(
        job_id=job_id,
        total=total_info["qtd"],
        offset=offset,
        limit=limit,
        items=[TransactionItem(**r) for r in rows],
        categorias_disponiveis=CATEGORY_LABELS,
    )
