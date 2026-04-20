from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.domain.schemas import JobProgressEvent, JobStatus


@dataclass
class JobState:
    job_id: str
    filename: str
    status: JobStatus = "queued"
    progress: int = 0
    message: str = "Job enfileirado"
    error: str | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    queues: list[asyncio.Queue[JobProgressEvent]] = field(default_factory=list)
    terminal: bool = False


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobState] = {}
        self._lock = asyncio.Lock()

    async def create(self, job_id: str, filename: str) -> JobState:
        async with self._lock:
            state = JobState(job_id=job_id, filename=filename)
            self._jobs[job_id] = state
            return state

        #Busca job na RAM ou tenta recuperar do banco de dados
    async def get(self, job_id: str) -> JobState | None:
        # 1. Tenta cache na RAM
        state = self._jobs.get(job_id)
        if state:
            return state

        # 2. Se nao estiver na RAM, tenta recuperar do DB
        from app.infrastructure.db import fetch_job_status
        db_job = await fetch_job_status(job_id)
        if not db_job:
            return None

        # 3. Hidrata na RAM para futuras consultas e SSE
        async with self._lock:
            # Re-checa apos o lock para evitar race conditions
            if job_id in self._jobs:
                return self._jobs[job_id]

            state = JobState(
                job_id=job_id,
                filename=db_job["filename"],
                status=db_job["status"],
                message="Retomado do histórico" if db_job["status"] == "done" else "Sessão recuperada",
                error=db_job["error"],
                updated_at=db_job["updated_at"],
                terminal=(db_job["status"] in ("done", "failed")),
            )
            # Se ja estiver pronto, colocamos progresso em 100
            if state.status == "done":
                state.progress = 100
                state.message = "Processamento concluído"

            self._jobs[job_id] = state
            return state

    async def subscribe(self, job_id: str) -> asyncio.Queue[JobProgressEvent] | None:
        state = await self.get(job_id)
        if state is None:
            return None
        q: asyncio.Queue[JobProgressEvent] = asyncio.Queue(maxsize=64)
        await q.put(
            JobProgressEvent(
                job_id=job_id,
                status=state.status,
                progress=state.progress,
                message=state.message,
            )
        )
        if not state.terminal:
            state.queues.append(q)
        return q

    def unsubscribe(self, job_id: str, q: asyncio.Queue) -> None:
        state = self._jobs.get(job_id)
        if state and q in state.queues:
            state.queues.remove(q)

    async def publish(
        self,
        job_id: str,
        status: JobStatus,
        progress: int,
        message: str,
        error: str | None = None,
    ) -> None:
        state = self._jobs.get(job_id)
        if state is None:
            return
        state.status = status
        state.progress = max(0, min(100, progress))
        state.message = message
        state.error = error
        state.updated_at = datetime.now(UTC)
        if status in ("done", "failed"):
            state.terminal = True

        event = JobProgressEvent(
            job_id=job_id,
            status=status,
            progress=state.progress,
            message=message,
        )
        for q in list(state.queues):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass


job_store = JobStore()
