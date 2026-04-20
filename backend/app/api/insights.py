import asyncio

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.auth import require_api_key
from app.domain.schemas import AdvancedInsightsResponse
from app.services.metrics_cache import get_advanced_metrics_cached

router = APIRouter(prefix="/api", tags=["insights"], dependencies=[Depends(require_api_key)])


@router.get("/insights/advanced/{job_id}", response_model=AdvancedInsightsResponse)
async def advanced_insights(job_id: str, response: Response) -> AdvancedInsightsResponse:
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    metrics = await asyncio.to_thread(get_advanced_metrics_cached, job_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="Job não encontrado ou sem transações.")
    return AdvancedInsightsResponse(job_id=job_id, metrics=metrics)
