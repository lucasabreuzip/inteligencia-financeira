"""
Fachada de compatibilidade da camada de infraestrutura de banco de dados.
"""
from __future__ import annotations

# Pool management & connection context managers
from .pool import (
    async_connection,
    close_pools,
    init_async_pool,
    init_db,
    sync_connection,
)

# Data access (repositories)
from .repositories import (
    fetch_ai_insights_json,
    fetch_dashboard,
    fetch_job_status,
    fetch_latest_job,
    save_kpis,
    save_timeseries,
    save_transactions,
    upsert_job,
)

__all__ = [
    # Pool
    "init_db",
    "init_async_pool",
    "close_pools",
    "sync_connection",
    "async_connection",
    # Repositories
    "upsert_job",
    "save_kpis",
    "save_timeseries",
    "save_transactions",
    "fetch_job_status",
    "fetch_dashboard",
    "fetch_ai_insights_json",
    "fetch_latest_job",
]
