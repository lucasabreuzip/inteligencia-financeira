"""
Cache TTL thread-safe para payloads pesados de chat/agent por job_id.
"""
from __future__ import annotations

import logging
import time
from collections import OrderedDict
from threading import Lock
from typing import Any
from collections.abc import Callable

import pandas as pd
from psycopg.rows import dict_row

from app.infrastructure.db import sync_connection
from app.services.advanced_metrics import build_advanced_metrics
from app.services.dataset_stats import fetch_dataset_snapshot

logger = logging.getLogger(__name__)

    # Cache LRU + TTL minimalista, thread-safe
class _TTLCache:

    def __init__(self, maxsize: int, ttl_sec: float) -> None:
        self._maxsize = maxsize
        self._ttl = ttl_sec
        self._lock = Lock()
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()

    def get(self, key: str) -> Any | None:
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at < now:
                # Lazy eviction: expirou, remove e devolve None
                self._store.pop(key, None)
                return None
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        expires_at = time.monotonic() + self._ttl
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
            self._store[key] = (expires_at, value)
            while len(self._store) > self._maxsize:
                self._store.popitem(last=False)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)


# TTL de 1h: um job tipicamente e consultado em sessoes curtas (<30min).
# maxsize=32: cabe confortavelmente em RAM (~5MB/job de metrics json).
_ADVANCED_METRICS_CACHE = _TTLCache(maxsize=32, ttl_sec=3600.0)
_SNAPSHOT_CACHE = _TTLCache(maxsize=32, ttl_sec=3600.0)


# Apos migracao DATE: psycopg3 retorna datetime.date, que
# pd.to_datetime abaixo aceita diretamente. Nao precisa de TO_CHAR
# aqui porque construimos pd.Timestamp internamente - formato
# string so interessa para consumidores de API.
def _compute_advanced_metrics(job_id: str) -> dict:
    with sync_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT id, valor, data, status, cliente, descricao, categoria "
                "FROM transactions WHERE job_id = %s",
                (job_id,),
            )
            rows = cur.fetchall()
    df = pd.DataFrame(rows)
    if df.empty:
        return {}
    df["data"] = pd.to_datetime(df["data"])
    df["valor"] = df["valor"].astype(float)
    return build_advanced_metrics(df)


def _cached_or_compute(
    cache: _TTLCache, key: str, compute: Callable[[str], Any], label: str
) -> Any:
    cached = cache.get(key)
    if cached is not None:
        logger.debug("cache hit: %s job=%s", label, key)
        return cached
    logger.info("cache miss: %s job=%s — computando", label, key)
    value = compute(key)
    cache.set(key, value)
    return value

    # versao cacheada de build_advanced_metrics para reuso em chat multi-turno
def get_advanced_metrics_cached(job_id: str) -> dict:
    return _cached_or_compute(
        _ADVANCED_METRICS_CACHE, job_id, _compute_advanced_metrics, "advanced_metrics"
    )

    #versao cacheada de fetch_dataset_snapshot - idem, invariante pos-ingestao
def get_dataset_snapshot_cached(job_id: str) -> dict:
    return _cached_or_compute(
        _SNAPSHOT_CACHE, job_id, fetch_dataset_snapshot, "dataset_snapshot"
    )

    # Hook para futura re-ingestao do mesmo job_id. Hoje nao e chamado
def invalidate_job_cache(job_id: str) -> None:
    _ADVANCED_METRICS_CACHE.invalidate(job_id)
    _SNAPSHOT_CACHE.invalidate(job_id)
    logger.info("cache invalidado para job=%s", job_id)
