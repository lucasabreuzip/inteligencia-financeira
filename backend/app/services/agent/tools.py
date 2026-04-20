"""
Dispatch e execução das ferramentas chamadas pelo agente.

Cada ferramenta mapeia para uma query SQL, busca vetorial ou acesso a cache.
O dispatch centralizado (`run_tool`) garante que todas as ferramentas
registram fontes no AgentContext e logam resultados de forma consistente.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.infrastructure.db import fetch_ai_insights_json
from app.services.embedding_client import get_embedding_client
from app.services.sql_tools import (
    aggregate_transactions,
    count_transactions,
    list_transactions,
    semantic_search_db,
)

from .context import AgentContext, ingest_advanced_metrics_ids

logger = logging.getLogger(__name__)

    # Executa uma ferramenta pelo nome e atualiza o contexto com os resultados
def run_tool(name: str, args: dict[str, Any], ctx: AgentContext) -> Any:
    if name == "list_transactions":
        order_by = args.pop("order_by", "data")
        order_dir = args.pop("order_dir", "desc")
        limit = args.pop("limit", 50)
        rows = list_transactions(
            ctx.job_id, filters=args,
            order_by=order_by, order_dir=order_dir, limit=limit,
        )
        ctx.add_rows(rows)
        return {"rows": rows, "returned": len(rows)}

    if name == "fetch_ai_diagnostics":
        try:
            raw = fetch_ai_insights_json(ctx.job_id)
        except Exception as e:
            return {"error": str(e)}
        if raw:
            return {"ai_insights": json.loads(raw)}
        return {"ai_insights": "Nenhum diagnóstico oficial IA encontrado para este job."}

    if name == "count_transactions":
        return count_transactions(ctx.job_id, filters=args)

    if name == "aggregate_transactions":
        group_by = args.pop("group_by")
        metric = args.pop("metric")
        limit = args.pop("limit", 20)
        return {
            "group_by": group_by,
            "metric": metric,
            "result": aggregate_transactions(
                ctx.job_id,
                group_by=group_by, metric=metric, filters=args, limit=limit,
            ),
        }

    if name == "get_advanced_metrics":
        metrics = ctx.get_advanced_metrics()
        if not metrics:
            return {"error": "Sem transações para calcular métricas."}
        section = args.get("section", "all")
        if section == "all" or section not in metrics:
            payload = {"section": "all", "data": metrics}
        else:
            payload = {"section": section, "data": metrics[section]}
        ingest_advanced_metrics_ids(ctx, payload["data"])
        return payload

    if name == "semantic_search":
        query = args.get("query", "")
        if not query:
            return {"error": "Query vazia."}

        query_vector = get_embedding_client().embed_query(query)

        k = int(args.get("k", 10))
        categoria_filter = (args.get("categoria") or "").lower().strip() or None
        relevance_threshold = float(args.get("relevance_threshold", 1.2))

        matches, quality = semantic_search_db(
            ctx.job_id,
            query_vector,
            k=k,
            categoria=categoria_filter,
            relevance_threshold=relevance_threshold,
        )

        for m in matches:
            ctx.add_rows([m], score=round(float(m["distance_score"]), 4))

        return {
            "matches": matches,
            "returned": len(matches),
            "qualidade_relevancia": quality,
            "observacao": (
                "Resultados com baixa relevância — considere usar list_transactions "
                "com filtros específicos." if quality in ("fraca", "nenhuma") else ""
            ),
        }

    return {"error": f"Ferramenta desconhecida: {name}"}

    # resumo curto do retorno para log/UI, evita expor payloads enormes
def summarize_tool_result(name: str, result: Any) -> str:
    if isinstance(result, dict):
        if "error" in result:
            return f"erro: {result['error']}"
        if name == "list_transactions":
            return f"{result.get('returned', 0)} linha(s)"
        if name == "count_transactions":
            return f"qtd={result.get('qtd')} soma={result.get('soma')}"
        if name == "aggregate_transactions":
            return f"{len(result.get('result', []))} grupo(s)"
        if name == "get_advanced_metrics":
            return f"seção={result.get('section')}"
        if name == "semantic_search":
            return (
                f"{result.get('returned', 0)} match(es) "
                f"[{result.get('qualidade_relevancia')}]"
            )
    return "ok"
