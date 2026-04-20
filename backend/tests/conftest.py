from __future__ import annotations

import os
import sys
import types

os.environ.setdefault(
    "DATABASE_URL", "postgresql://test:test@127.0.0.1:5432/test_db"
)
os.environ.setdefault("OPENAI_API_KEY", "")  # força caminhos offline
os.environ.setdefault("API_KEY", "")  # auth desabilitada nos testes
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")


def _install_psycopg_stub() -> None:
    """Evita ModuleNotFoundError quando o driver nativo nao esta presente."""
    if "psycopg" in sys.modules:
        return

    psycopg = types.ModuleType("psycopg")

    class _Connection: ...
    class _AsyncConnection:
        @classmethod
        async def connect(cls, *a, **k): raise RuntimeError("stub")

    psycopg.Connection = _Connection
    psycopg.AsyncConnection = _AsyncConnection

    def _connect(*a, **k): raise RuntimeError("psycopg stub: conexao real desabilitada nos testes")
    psycopg.connect = _connect

    rows = types.ModuleType("psycopg.rows")
    rows.dict_row = lambda *a, **k: None
    psycopg.rows = rows

    pool = types.ModuleType("psycopg_pool")

    class _ConnectionPool: ...
    class _AsyncConnectionPool: ...

    pool.ConnectionPool = _ConnectionPool
    pool.AsyncConnectionPool = _AsyncConnectionPool

    sys.modules["psycopg"] = psycopg
    sys.modules["psycopg.rows"] = rows
    sys.modules["psycopg_pool"] = pool


_install_psycopg_stub()
