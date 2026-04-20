from __future__ import annotations

import json
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient


SESSION = "abc-123-session"


def _parse_sse_frames(body: str) -> list[dict]:
    frames = []
    for raw in body.split("\n\n"):
        raw = raw.strip()
        if not raw.startswith("data:"):
            continue
        payload = raw[len("data:"):].strip()
        frames.append(json.loads(payload))
    return frames


@pytest.fixture
def client(monkeypatch):

    from app.main import app

    return TestClient(app)


@pytest.fixture
def fake_history(monkeypatch):

    recorder = {"loaded_for": [], "appended": []}

    async def fake_load(job_id, session_id):
        recorder["loaded_for"].append((job_id, session_id))
        return recorder.get("preload", [])

    async def fake_append(job_id, session_id, question, answer):
        recorder["appended"].append({
            "job_id": job_id, "session_id": session_id,
            "question": question, "answer": answer,
        })

    from app.api import chat as chat_module
    monkeypatch.setattr(chat_module, "load_history", fake_load)
    monkeypatch.setattr(chat_module, "append_exchange", fake_append)
    return recorder


def test_chat_stream_happy_path(client, monkeypatch, fake_history):

    from app.api import chat as chat_module

    events = [
        {"type": "token", "delta": "Olá"},
        {"type": "tool_start", "name": "count_transactions", "args": {"status": "pago"}, "call_id": "c1"},
        {"type": "tool_end", "name": "count_transactions", "ok": True, "summary": "qtd=42", "call_id": "c1"},
        {"type": "token", "delta": ", total 42."},
        {
            "type": "done",
            "response": {
                "job_id": "j1", "question": "q", "answer": "Olá, total 42.",
                "sources": [], "tools_used": [],
                "grounding": {"cited": [], "verified": [], "unverified": [], "is_grounded": True},
            },
        },
    ]

    async def fake_stream(job_id, question, top_k, history) -> AsyncIterator[dict]:
        for ev in events:
            yield ev

    monkeypatch.setattr(chat_module, "run_agent_stream", fake_stream)

    resp = client.post(
        "/api/chat/stream",
        json={"job_id": "j1", "session_id": SESSION, "question": "quantos pagos?", "top_k": 5},
    )

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert resp.headers["cache-control"] == "no-cache, no-transform"
    assert resp.headers["x-accel-buffering"] == "no"

    frames = _parse_sse_frames(resp.text)
    assert frames == events
    assert [f["type"] for f in frames] == [
        "token", "tool_start", "tool_end", "token", "done"
    ]

    # Historico foi carregado antes do agente
    assert fake_history["loaded_for"] == [("j1", SESSION)]
    # Exchange persistido apos `done` com a answer final
    assert len(fake_history["appended"]) == 1
    assert fake_history["appended"][0]["answer"] == "Olá, total 42."
    assert fake_history["appended"][0]["session_id"] == SESSION


def test_chat_stream_agent_unavailable_emits_error_frame(client, monkeypatch, fake_history):
    from app.api import chat as chat_module
    from app.services.agent import AgentUnavailableError

    async def fake_stream(job_id, question, top_k, history) -> AsyncIterator[dict]:
        raise AgentUnavailableError("OPENAI_API_KEY nao configurada no backend.")
        yield  # pragma: no cover

    monkeypatch.setattr(chat_module, "run_agent_stream", fake_stream)

    resp = client.post(
        "/api/chat/stream",
        json={"job_id": "j1", "session_id": SESSION, "question": "pergunta valida", "top_k": 5},
    )

    assert resp.status_code == 200
    frames = _parse_sse_frames(resp.text)
    assert len(frames) == 1
    assert frames[0]["type"] == "error"
    assert "OPENAI_API_KEY" in frames[0]["message"]
    # Sem `done` -> sem persistencia
    assert fake_history["appended"] == []


def test_chat_stream_unhandled_exception_emits_error_frame(client, monkeypatch, fake_history):
    from app.api import chat as chat_module

    async def fake_stream(job_id, question, top_k, history) -> AsyncIterator[dict]:
        yield {"type": "token", "delta": "parcial"}
        raise RuntimeError("boom interno")

    monkeypatch.setattr(chat_module, "run_agent_stream", fake_stream)

    resp = client.post(
        "/api/chat/stream",
        json={"job_id": "j1", "session_id": SESSION, "question": "pergunta valida", "top_k": 5},
    )

    assert resp.status_code == 200
    frames = _parse_sse_frames(resp.text)
    types = [f["type"] for f in frames]
    assert "token" in types
    assert types[-1] == "error"
    assert "boom interno" in frames[-1]["message"]
    # Exception no meio -> NAO persiste
    assert fake_history["appended"] == []


def test_chat_stream_rejects_short_question(client):
    """Validacao pydantic: question com <3 chars rejeitada antes do stream."""
    resp = client.post(
        "/api/chat/stream",
        json={"job_id": "j1", "session_id": SESSION, "question": "oi", "top_k": 5},
    )
    assert resp.status_code == 422


def test_chat_stream_rejects_missing_session_id(client):
    """session_id agora eh obrigatorio no payload."""
    resp = client.post(
        "/api/chat/stream",
        json={"job_id": "j1", "question": "pergunta valida", "top_k": 5},
    )
    assert resp.status_code == 422


def test_chat_sync_endpoint_surfaces_agent_unavailable(client, monkeypatch, fake_history):
    """/api/chat (sync) deve converter AgentUnavailableError em HTTP 409."""
    from app.api import chat as chat_module
    from app.services.agent import AgentUnavailableError

    def fake_run_agent(job_id, question, top_k, history):
        raise AgentUnavailableError("OPENAI_API_KEY nao configurada.")

    monkeypatch.setattr(chat_module, "run_agent", fake_run_agent)

    resp = client.post(
        "/api/chat",
        json={"job_id": "j1", "session_id": SESSION, "question": "pergunta valida", "top_k": 5},
    )
    assert resp.status_code == 409
    assert "OPENAI_API_KEY" in resp.json()["detail"]
    assert fake_history["appended"] == []


def test_chat_sync_persists_exchange_on_success(client, monkeypatch, fake_history):
    from app.api import chat as chat_module
    from app.domain.chat_schemas import ChatResponse, GroundingInfo

    expected_answer = "Receita total: R$ 120.000,00."

    def fake_run_agent(job_id, question, top_k, history):
        return ChatResponse(
            job_id=job_id, question=question, answer=expected_answer,
            sources=[], tools_used=[], grounding=GroundingInfo(),
        )

    monkeypatch.setattr(chat_module, "run_agent", fake_run_agent)

    resp = client.post(
        "/api/chat",
        json={"job_id": "j1", "session_id": SESSION, "question": "qual a receita?", "top_k": 5},
    )
    assert resp.status_code == 200
    assert resp.json()["answer"] == expected_answer

    # Load antes, persist depois
    assert fake_history["loaded_for"] == [("j1", SESSION)]
    assert len(fake_history["appended"]) == 1
    assert fake_history["appended"][0] == {
        "job_id": "j1", "session_id": SESSION,
        "question": "qual a receita?", "answer": expected_answer,
    }


def test_chat_history_endpoint_returns_messages(client, monkeypatch):
    from app.api import chat as chat_module

    sample = [
        {"role": "user", "content": "qual a receita?"},
        {"role": "assistant", "content": "R$ 120.000,00"},
        {"role": "user", "content": "e o DSO?"},
        {"role": "assistant", "content": "45 dias"},
    ]

    async def fake_load(job_id, session_id):
        return sample

    monkeypatch.setattr(chat_module, "load_history", fake_load)

    resp = client.get(f"/api/chat/history/j1/{SESSION}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job_id"] == "j1"
    assert body["session_id"] == SESSION
    assert body["messages"] == sample


def test_chat_history_endpoint_empty_session(client, monkeypatch):
    from app.api import chat as chat_module

    async def fake_load(job_id, session_id):
        return []

    monkeypatch.setattr(chat_module, "load_history", fake_load)

    resp = client.get(f"/api/chat/history/j1/{SESSION}")
    assert resp.status_code == 200
    assert resp.json()["messages"] == []
