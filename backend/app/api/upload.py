import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Request, UploadFile, status

from app.core.auth import require_api_key
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.domain.schemas import JobCreatedResponse
from app.infrastructure.db import sync_connection, upsert_job
from app.infrastructure.job_store import job_store
from app.workers.ingestion import run_ingestion_pipeline

router = APIRouter(prefix="/api", tags=["ingestion"], dependencies=[Depends(require_api_key)])


@router.post("/upload", response_model=JobCreatedResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(lambda: get_settings().upload_rate_limit)
async def upload_csv(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> JobCreatedResponse:
    settings = get_settings()

    filename = file.filename or "upload.csv"
    ext = Path(filename).suffix.lower()
    if ext not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(
            status_code=415, detail="Apenas arquivos .csv, .xlsx ou .xls são aceitos."
        )

    max_bytes = settings.max_upload_mb * 1024 * 1024
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo excede o limite de {settings.max_upload_mb}MB.",
        )

    job_id = uuid.uuid4().hex
    dest_path: Path = settings.upload_dir / f"{job_id}{ext}"

    total = 0
    try:
        with dest_path.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    out.close()
                    dest_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"Arquivo excede o limite de {settings.max_upload_mb}MB.",
                    )
                out.write(chunk)
    finally:
        await file.close()

    if total == 0:
        dest_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail="Arquivo vazio.")

    await job_store.create(job_id, filename)
    with sync_connection() as conn:
        upsert_job(conn, job_id, filename, status="queued")

    background_tasks.add_task(run_ingestion_pipeline, job_id, dest_path)

    return JobCreatedResponse(job_id=job_id, status="queued", filename=filename)
