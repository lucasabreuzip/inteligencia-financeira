import asyncio
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.core.auth import require_api_key
from app.core.config import get_settings
from app.core.constants import CHAT_TIMEOUT_SEC
from app.core.rate_limit import limiter
from app.domain.chat_schemas import ChatHistoryResponse, ChatMessage, ChatRequest, ChatResponse
from app.services.agent import AgentUnavailableError, run_agent, run_agent_stream
from app.services.chat_history import append_exchange, load_history

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"], dependencies=[Depends(require_api_key)])


@router.post("/chat", response_model=ChatResponse)
@limiter.limit(lambda: get_settings().chat_rate_limit)
async def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    try:
        history = await load_history(payload.job_id, payload.session_id)
        async with asyncio.timeout(CHAT_TIMEOUT_SEC):
            response = await asyncio.to_thread(
                run_agent, payload.job_id, payload.question, payload.top_k, history
            )
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="A análise excedeu o tempo limite. Tente uma pergunta mais específica.",
        )
    except AgentUnavailableError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("Falha no agent")
        raise HTTPException(status_code=500, detail=f"Erro no agent: {exc}")

    # Persistencia pos-sucesso: se o agente falhar, nao gravamos exchange
    # incompleta. `append_exchange` ja e defensivo contra erros de DB.
    await append_exchange(
        payload.job_id, payload.session_id, payload.question, response.answer
    )
    return response


def _sse_format(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"

#Streaming SSE do agente. Emite tokens + eventos de tool_call ao vivo.
@router.post("/chat/stream")
@limiter.limit(lambda: get_settings().chat_rate_limit)
async def chat_stream(request: Request, payload: ChatRequest) -> StreamingResponse:
   
    async def event_gen():
        final_answer: str | None = None
        try:
            history = await load_history(payload.job_id, payload.session_id)
            async for event in run_agent_stream(
                payload.job_id, payload.question, payload.top_k, history
            ):
                if event.get("type") == "done":
                    resp = event.get("response") or {}
                    final_answer = resp.get("answer")
                yield _sse_format(event)
        except AgentUnavailableError as exc:
            yield _sse_format({"type": "error", "message": str(exc)})
        except asyncio.CancelledError:
            # Cliente desconectou - propaga para cancelar streams OpenAI subjacentes.
            logger.info("chat_stream cancelado pelo cliente job=%s", payload.job_id)
            raise
        except Exception as exc:
            logger.exception("Falha no chat_stream job=%s", payload.job_id)
            yield _sse_format({"type": "error", "message": f"Erro no agent: {exc}"})
        else:
            if final_answer is not None:
                await append_exchange(
                    payload.job_id, payload.session_id, payload.question, final_answer
                )

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",  # desliga buffering de proxies tipo nginx
            "Connection": "keep-alive",
        },
    )

#Rehidrata transcricao da sessao para a UI apos reload/limpeza de cache
@router.get("/chat/history/{job_id}/{session_id}", response_model=ChatHistoryResponse)
async def get_chat_history(job_id: str, session_id: str) -> ChatHistoryResponse:
    rows = await load_history(job_id, session_id)
    return ChatHistoryResponse(
        job_id=job_id,
        session_id=session_id,
        messages=[ChatMessage(role=r["role"], content=r["content"]) for r in rows],
    )
