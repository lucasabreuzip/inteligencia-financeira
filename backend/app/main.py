from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from app.api.chat import router as chat_router
from app.api.dashboard import router as dashboard_router
from app.api.insights import router as insights_router
from app.api.status import router as status_router
from app.api.transactions import router as transactions_router
from app.api.upload import router as upload_router
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.infrastructure.db import close_pools, init_async_pool, init_db
from app.services.observability import flush as flush_langfuse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger = logging.getLogger(__name__)
    try:
        init_db(settings.database_url)
        await init_async_pool()
        logger.info("Servidor inicializado com SUCESSO em modo %s", settings.app_env)
    except Exception as e:
        logger.error("FALHA NA INICIALIZACAO: %s", str(e), exc_info=True)
        raise e
    try:
        yield
    finally:
        flush_langfuse()
        await close_pools()


app = FastAPI(
    title="Plataforma de Inteligência Financeira",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_settings = get_settings()
_cors_origins = _settings.cors_origin_list
if "*" in _cors_origins:
    raise RuntimeError("Combinado com credentials eh proibido pela spec CORS. ")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

app.include_router(upload_router)
app.include_router(status_router)
app.include_router(dashboard_router)
app.include_router(transactions_router)
app.include_router(insights_router)
app.include_router(chat_router)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
