from __future__ import annotations

import asyncio
import datetime as dt
from contextlib import contextmanager
from pathlib import Path
from textwrap import dedent

import pytest


@contextmanager
def _fake_conn(recorder: dict):

    class _Cur:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def execute(self, *a, **k): recorder.setdefault("cur_exec", []).append(a)
        def executemany(self, sql, rows):
            recorder.setdefault("cur_execmany", []).append((sql, list(rows)))

        @contextmanager
        def copy(self, sql):
            recorder.setdefault("copy_sql", []).append(sql)
            writes = []
            recorder.setdefault("copy_rows", []).append(writes)

            class _Cp:
                def write_row(self, row): writes.append(row)
            yield _Cp()

    class _Conn:
        def execute(self, *a, **k): recorder.setdefault("exec", []).append(a)
        def cursor(self): return _Cur()

        @contextmanager
        def transaction(self): yield

    yield _Conn()


def _make_csv(tmp_path: Path) -> Path:

    content = dedent(
        """\
        id;valor;data;status;cliente;descricao
        txn_001;1500,00;2025-01-05;pago;ACME Ltda;Contratacao servico de nuvem
        txn_002;2000,00;2025-01-20;pendente;Beta SA;Renovacao licenca ERP
        txn_003;500,00;2025-02-10;pago;ACME Ltda;Suporte premium mensal
        txn_004;1200,00;2025-02-15;atrasado;Gamma LLC;Consultoria tecnica
        txn_005;800,00;2025-03-01;pago;Delta Corp;Manutencao sistema
        txn_006;950,00;2025-03-10;pendente;Epsilon;Assinatura plataforma
        """
    )
    f = tmp_path / "sample.csv"
    f.write_text(content, encoding="utf-8-sig")
    return f


@pytest.fixture
def fake_db(monkeypatch):

    recorder: dict = {
        "kpis": None,
        "timeseries": [],
        "transactions": [],
        "job_upserts": [],
    }

    def fake_sync_connection():
        return _fake_conn(recorder)

    def fake_upsert_job(conn, job_id, filename, status, error=None):
        recorder["job_upserts"].append(
            {"job_id": job_id, "filename": filename, "status": status, "error": error}
        )

    def fake_save_kpis(conn, job_id, kpis, insights_json):
        recorder["kpis"] = {"job_id": job_id, "kpis": kpis, "insights_json": insights_json}

    def fake_save_transactions(conn, job_id, rows):
        recorder["transactions"] = list(rows)

    def fake_save_timeseries(conn, job_id, rows):
        recorder["timeseries"] = list(rows)

    # Patch no modulo `workers.ingestion` — ponto de uso.
    from app.workers import ingestion as ing

    monkeypatch.setattr(ing, "sync_connection", fake_sync_connection)
    monkeypatch.setattr(ing, "upsert_job", fake_upsert_job)
    monkeypatch.setattr(ing, "save_kpis", fake_save_kpis)
    monkeypatch.setattr(ing, "save_transactions", fake_save_transactions)
    monkeypatch.setattr(ing, "save_timeseries", fake_save_timeseries)
    return recorder


@pytest.fixture
def fake_llm(monkeypatch):

    from app.workers import ingestion as ing

    async def fake_build_vector_index(job_id, on_progress=None):
        return 0

    monkeypatch.setattr(ing, "generate_insights", lambda summary: None)
    monkeypatch.setattr(ing, "build_vector_index", fake_build_vector_index)


def test_pipeline_end_to_end_happy_path(tmp_path, fake_db, fake_llm):

    from app.infrastructure.job_store import job_store
    from app.workers.ingestion import run_ingestion_pipeline

    async def _scenario():
        csv_path = _make_csv(tmp_path)
        job_id = "test-e2e-happy"
        await job_store.create(job_id, "sample.csv")
        await run_ingestion_pipeline(job_id, csv_path)
        return await job_store.get(job_id)

    state = asyncio.run(_scenario())

    # Estado terminal consistente
    assert state is not None
    assert state.status == "done"
    assert state.progress == 100
    assert state.terminal is True
    assert state.error is None

    # KPIs foram computados pelo codigo real (nao mock)
    kpis = fake_db["kpis"]["kpis"]
    # 2 meses apos _drop_last_month (marco foi descartado)
    assert kpis["total_transacoes"] == 4  # txn_001..004
    assert kpis["receita_total"] == 2000.0  # txn_001 + txn_003
    assert kpis["periodo_inicio"] == "2025-01-05"
    assert kpis["periodo_fim"] == "2025-02-15"
    # Sem OPENAI_API_KEY -> insights=None -> insights_json=None
    assert fake_db["kpis"]["insights_json"] is None

    # save_transactions recebe tuplas com `data` do tipo datetime.date (schema DATE)
    assert len(fake_db["transactions"]) == 4
    for row in fake_db["transactions"]:
        # row = (id, job_id, valor, data, status, cliente, descricao, categoria)
        assert isinstance(row[3], dt.date)
        assert row[1] == "test-e2e-happy"

    # Timeseries tem exatamente 2 meses (jan + fev) apos drop do mes parcial
    ts_periods = [r[0] for r in fake_db["timeseries"]]
    assert ts_periods == sorted(ts_periods)
    assert len(ts_periods) == 2

    # upsert_job foi chamado para persisting e done
    statuses = [u["status"] for u in fake_db["job_upserts"]]
    assert "persisting" in statuses
    assert "done" in statuses


def test_pipeline_emits_progress_transitions(tmp_path, fake_db, fake_llm):

    from app.infrastructure.job_store import job_store
    from app.workers.ingestion import run_ingestion_pipeline

    seen: list[str] = []

    async def _scenario():
        csv_path = _make_csv(tmp_path)
        job_id = "test-transitions"
        await job_store.create(job_id, "sample.csv")

        # Assina a fila para capturar todos os eventos publicados.
        q = await job_store.subscribe(job_id)
        assert q is not None

        task = asyncio.create_task(run_ingestion_pipeline(job_id, csv_path))
        # Drena a fila enquanto pipeline roda.
        while True:
            try:
                ev = await asyncio.wait_for(q.get(), timeout=2.0)
            except asyncio.TimeoutError:
                break
            seen.append(ev.status)
            if ev.status in ("done", "failed"):
                break
        await task

    asyncio.run(_scenario())

    # Fases obrigatorias do contrato de UX.
    for phase in ("reading", "cleaning", "computing", "ai", "persisting", "embedding", "done"):
        assert phase in seen, f"fase '{phase}' ausente em {seen}"


def test_pipeline_reports_etl_error_as_failed(tmp_path, fake_db, fake_llm):

    from app.infrastructure.job_store import job_store
    from app.workers.ingestion import run_ingestion_pipeline

    bad = tmp_path / "bad.csv"
    bad.write_text("id;valor;data\ntxn_001;100;2025-01-01\n", encoding="utf-8")

    async def _scenario():
        job_id = "test-failed"
        await job_store.create(job_id, "bad.csv")
        await run_ingestion_pipeline(job_id, bad)
        return await job_store.get(job_id)

    state = asyncio.run(_scenario())

    assert state is not None
    assert state.status == "failed"
    assert state.error is not None
    assert "Colunas obrigatórias" in state.error or "obrigat" in state.error.lower()
