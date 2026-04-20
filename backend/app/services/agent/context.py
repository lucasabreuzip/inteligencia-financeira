"""Contexto acumulado durante a execução do agente RAG.
"""
from __future__ import annotations

from typing import Any

from app.domain.chat_schemas import ChatSource, ToolCallLog
from app.services.metrics_cache import get_advanced_metrics_cached

    #Acumula fontes devolvidas pelas ferramentas ao longo das iterações
class AgentContext:

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        self.sources: dict[str, ChatSource] = {}
        self.tool_calls: list[ToolCallLog] = []

    def get_advanced_metrics(self) -> dict:
        # Delega para o cache cross-request: em chat multi-turno o mesmo job_id
        # reusa o payload ja computado (invariante pos-ingestao).
        return get_advanced_metrics_cached(self.job_id)

    def add_rows(self, rows: list[dict], score: float | None = None) -> None:
        for r in rows:
            if "id" not in r or "valor" not in r:
                continue
            key = str(r["id"])
            if key in self.sources:
                continue
            self.sources[key] = ChatSource(
                id=key,
                valor=float(r["valor"]),
                data=str(r.get("data", "")),
                status=str(r.get("status", "")),
                cliente=str(r.get("cliente", "")),
                descricao=str(r.get("descricao", "")),
                score=score,
            )

    def log_tool(self, name: str, args: dict, ok: bool, summary: str | None = None) -> None:
        self.tool_calls.append(
            ToolCallLog(name=name, args=args, ok=ok, summary=summary)
        )

    def source_list(self, limit: int = 200) -> list[ChatSource]:
        items = list(self.sources.values())
        items.sort(key=lambda s: (s.score is None, s.score if s.score is not None else 0.0))
        return items[:limit]


def ingest_advanced_metrics_ids(ctx: AgentContext, payload: Any) -> None:
    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if "id" in node and "valor" in node:
                ctx.add_rows([node])
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for v in node:
                _walk(v)

    _walk(payload)
