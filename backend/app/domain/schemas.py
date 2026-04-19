from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class JobStatus(StrEnum):
    """Ciclo de vida de uma ingestão de CSV."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Job de ingestão — uma linha por upload de CSV."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: JobStatus
    filename: str
    rows_total: int = 0
    rows_processed: int = 0
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class TransactionItem(BaseModel):
    """Transação financeira normalizada — espelha o CSV de entrada."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    valor: Decimal
    data: date
    status: str
    cliente: str
    descricao: str | None = None


class DashboardKPIs(BaseModel):
    """KPIs agregados exibidos no topo do dashboard."""

    receita_total: Decimal = Field(description="Soma de todas as transações não canceladas.")
    receita_paga: Decimal = Field(description="Soma de transações com status pago.")
    receita_em_aberto: Decimal = Field(description="Soma de transações pendentes/atrasadas.")
    ticket_medio: Decimal
    qtd_transacoes: int
    qtd_clientes: int
    taxa_inadimplencia: float = Field(ge=0.0, le=1.0)