from __future__ import annotations

from fastapi import FastAPI

from app.api.routers import health

app = FastAPI(title="Inteligência Financeira API")

app.include_router(health.router)