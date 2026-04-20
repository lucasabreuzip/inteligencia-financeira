"""
Auth minima por API key compartilhada.
"""
from __future__ import annotations

import hmac
import logging

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, APIKeyQuery

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)
_query_scheme = APIKeyQuery(name="api_key", auto_error=False)


def require_api_key(
    request: Request,
    header_key: str | None = Depends(_header_scheme),
    query_key: str | None = Depends(_query_scheme),
) -> None:

    expected = get_settings().api_key
    if not expected:
        # Auth desabilitada em dev. Avisa uma vez por processo para nao spammar log.
        if not getattr(require_api_key, "_warned", False):
            logger.warning(
                "API_KEY vazia: autenticacao DESABILITADA."
            )
            require_api_key._warned = True  # type: ignore[attr-defined]
        return

    supplied = header_key or query_key
    if not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key invalida ou ausente.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
