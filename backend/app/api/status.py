import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from app.core.auth import require_api_key
from app.infrastructure.job_store import job_store

# SSE aceita api_key tambem via query (?api_key=...)
router = APIRouter(prefix="/api", tags=["status"], dependencies=[Depends(require_api_key)])

KEEPALIVE_INTERVAL_SEC = 15


async def _event_stream(request: Request, job_id: str) -> AsyncIterator[dict]:
    queue = await job_store.subscribe(job_id)
    if queue is None:
        return
    try:
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_INTERVAL_SEC)
            except asyncio.TimeoutError:
                yield {"event": "ping", "data": "{}"}
                continue

            yield {
                "event": "progress",
                "data": json.dumps(
                    {
                        "job_id": event.job_id,
                        "status": event.status,
                        "progress": event.progress,
                        "message": event.message,
                        "timestamp": event.timestamp.isoformat(),
                    }
                ),
            }
            if event.status in ("done", "failed"):
                break
    finally:
        job_store.unsubscribe(job_id, queue)


@router.get("/status/{job_id}")
async def stream_status(request: Request, job_id: str) -> EventSourceResponse:
    state = await job_store.get(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return EventSourceResponse(
        _event_stream(request, job_id),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/status/{job_id}/poll")
async def poll_status(job_id: str) -> dict:
    state = await job_store.get(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Job não encontrado.")
    return {
        "job_id": state.job_id,
        "status": state.status,
        "progress": state.progress,
        "filename": state.filename,
        "message": state.message,
        "timestamp": state.updated_at.isoformat(),
    }
