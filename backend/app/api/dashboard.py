from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_api_key
from app.domain.schemas import DashboardKPIs
from app.infrastructure.db import fetch_dashboard, fetch_latest_job

router = APIRouter(prefix="/api", tags=["dashboard"], dependencies=[Depends(require_api_key)])


@router.get("/dashboard/latest", response_model=DashboardKPIs)
async def get_latest_dashboard() -> DashboardKPIs:
    job_id = await fetch_latest_job()
    if job_id is None:
        raise HTTPException(status_code=404, detail="Nenhum job processado ainda.")
    data = await fetch_dashboard(job_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Dashboard indisponível.")
    return DashboardKPIs.model_validate(data)


@router.get("/dashboard/{job_id}", response_model=DashboardKPIs)
async def get_dashboard(job_id: str) -> DashboardKPIs:
    data = await fetch_dashboard(job_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Job não encontrado ou ainda não finalizado.")
    return DashboardKPIs.model_validate(data)
