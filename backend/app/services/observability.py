"""
Observabilidade LLM via Langfuse.

Ativacao: LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY no .env. Sem as duas,
tudo neste modulo e no-op — `get_openai_classes()` devolve o cliente original
e `@observe(...)` vira identidade.

O que a instrumentacao captura (quando habilitada):
  - Cada chamada a chat.completions.create() vira um `generation` Langfuse com
    latency, tokens in/out, modelo, custo USD estimado e conteudo das mensagens.
  - `@observe(name=...)` agrupa chamadas filhas sob um unico trace pai (ex.:
    `run_agent` pode fazer N chamadas OpenAI — todas ficam no mesmo trace).
  - `update_current_trace(metadata=...)` anexa dimensoes custom (job_id, etc).

Nao enviamos OPENAI_API_KEY ao Langfuse; apenas o trafego LLM e os metadados.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any
from collections.abc import Callable

from app.core.config import get_settings

logger = logging.getLogger(__name__)

    #Checagem unica (cached) + import defensivo
@lru_cache(maxsize=1)
def langfuse_enabled() -> bool:

    settings = get_settings()

    if not settings.langfuse_public_key:
        logger.info("Langfuse desabilitado: LANGFUSE_PUBLIC_KEY não configurada.")
        return False
    if not settings.langfuse_secret_key:
        logger.info("Langfuse desabilitado: LANGFUSE_SECRET_KEY não configurada.")
        return False

    try:
        import langfuse  # noqa: F401
        logger.info("Langfuse HABILITADO (host=%s)", settings.langfuse_host)
        return True
    except ImportError:
        logger.warning("LANGFUSE_* setadas mas pacote 'langfuse' nao instalado.")
        return False


@lru_cache(maxsize=1)
def get_openai_classes() -> tuple[type, type]:
    """Devolve (OpenAI, AsyncOpenAI) — langfuse-wrapped se habilitado.

    Usar: `OpenAI, AsyncOpenAI = get_openai_classes()` no topo do modulo.
    Como e cacheado, a decisao e feita 1x por processo.
    """
    if langfuse_enabled():
        try:
            # Drop-in compativel: mesma API do openai SDK + tracing automatico.
            from langfuse.openai import AsyncOpenAI as LFAsyncOpenAI
            from langfuse.openai import OpenAI as LFOpenAI
            return LFOpenAI, LFAsyncOpenAI
        except ImportError:
            logger.warning("langfuse.openai indisponivel; usando openai cru.")
    from openai import AsyncOpenAI, OpenAI
    return OpenAI, AsyncOpenAI


def observe(name: str | None = None, **kwargs: Any) -> Callable:
    """Decorator-factory compativel com `langfuse.decorators.observe`.

    Uso: `@observe(name="agent_run")`. Fora do Langfuse, e identidade - a
    funcao decorada nao paga nenhum custo extra.
    """
    if not langfuse_enabled():
        def identity(fn: Callable) -> Callable:
            return fn
        return identity
    try:
        from langfuse.decorators import observe as _lf_observe
        return _lf_observe(name=name, **kwargs) if name else _lf_observe(**kwargs)
    except ImportError:
        def identity(fn: Callable) -> Callable:
            return fn
        return identity


def update_current_trace(**kwargs: Any) -> None:
    """Anexa metadados ao trace corrente (ex.: user_id, session_id, tags).
    No-op se Langfuse desabilitado. Excecoes sao silenciadas — observabilidade
    nunca deve quebrar o fluxo principal.
    """
    if not langfuse_enabled():
        return
    try:
        from langfuse.decorators import langfuse_context
        langfuse_context.update_current_trace(**kwargs)
    except Exception:
        logger.debug("update_current_trace falhou", exc_info=True)


def flush() -> None:
    """Flush sincrono do batch de eventos Langfuse - chamar no shutdown para
    nao perder os ultimos traces em SIGTERM."""
    if not langfuse_enabled():
        return
    try:
        from langfuse import Langfuse
        Langfuse().flush()
    except Exception:
        logger.debug("langfuse.flush() falhou", exc_info=True)
