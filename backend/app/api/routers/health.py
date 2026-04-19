from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness — processo está de pé."""
    return {"status": "ok"}


@router.get("/health/db")
def health_db(db: Session = Depends(get_db)) -> dict[str, str]:
    """Readiness — banco responde. Separa liveness de readiness pra orquestrador
    reiniciar o container certo na hora certa."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "db": "ok"}