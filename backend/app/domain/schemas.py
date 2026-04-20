from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

JobStatus = Literal["queued", "reading", "cleaning", "computing", "persisting", "ai", "embedding", "done", "failed"]


class JobCreatedResponse(BaseModel):
    job_id: str
    status: JobStatus
    filename: str


class JobProgressEvent(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AIAlert(BaseModel):
    titulo: str
    severidade: Literal["baixa", "media", "alta"]
    descricao: str


class AIInsights(BaseModel):
    classificacao: Literal["saudavel", "atencao", "critico"]
    resumo: str
    alertas: list[AIAlert] = Field(min_length=0, max_length=5)


class TimeseriesPoint(BaseModel):
    periodo: str
    receita: float
    transacoes: int


class DashboardKPIs(BaseModel):
    job_id: str
    filename: str
    total_transacoes: int
    receita_total: float
    ticket_medio: float
    taxa_inadimplencia: float
    inadimplencia_valor: float
    periodo_inicio: str | None
    periodo_fim: str | None
    insights: AIInsights | None
    timeseries: list[TimeseriesPoint]


class TransactionItem(BaseModel):
    id: str
    valor: float
    data: str
    status: str
    cliente: str
    descricao: str
    categoria: str


class TransactionsPageResponse(BaseModel):
    job_id: str
    total: int
    offset: int
    limit: int
    items: list[TransactionItem]
    categorias_disponiveis: dict[str, str]


class AdvancedInsightsResponse(BaseModel):
    job_id: str
    metrics: dict
