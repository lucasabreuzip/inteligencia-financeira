"""
Gerenciamento de connection pools PostgreSQL (sync + async).
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager, contextmanager
from collections.abc import AsyncIterator, Iterator

import psycopg
from psycopg_pool import AsyncConnectionPool, ConnectionPool

from .schema import SCHEMA

logger = logging.getLogger(__name__)

_sync_pool: ConnectionPool | None = None
_async_pool: AsyncConnectionPool | None = None
_database_url: str | None = None


def _pool_bounds() -> tuple[int, int]:
    from app.core.config import get_settings
    s = get_settings()
    return s.db_pool_min, s.db_pool_max


def _build_sync_pool(database_url: str) -> ConnectionPool:
    min_size, max_size = _pool_bounds()
    kwargs = dict(
        min_size=min_size,
        max_size=max_size,
        timeout=30,
        max_idle=300,
        name="finance_sync_pool",
    )
    try:
        pool = ConnectionPool(database_url, open=False, **kwargs)
        pool.open(wait=True, timeout=10)
    except TypeError:
        # psycopg_pool < 3.2 não aceita `open=False` - nicializa implícito.
        pool = ConnectionPool(database_url, **kwargs)
        pool.wait(timeout=10)
    return pool


#Cria schema e abre o pool síncrono. Inclui retry para resiliência no boot.
def init_db(database_url: str) -> None:
    global _sync_pool, _database_url
    _database_url = database_url

    max_retries = 5
    retry_delay = 2

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            with psycopg.connect(database_url, autocommit=True) as conn:
                conn.execute(SCHEMA)
            logger.info("Banco de dados inicializado com sucesso na tentativa %d.", attempt)
            break
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                logger.warning(
                    "Falha ao conectar no banco (tentativa %d/%d). Retentando em %ds... Erro: %s",
                    attempt, max_retries, retry_delay, str(e)
                )
                import time
                time.sleep(retry_delay)
            else:
                logger.error("ERRO FATAL: Nao foi possivel inicializar o banco apos %d tentativas.", max_retries)
                raise last_error

    if _sync_pool is None:
        _sync_pool = _build_sync_pool(database_url)
        min_size, max_size = _pool_bounds()
        logger.info("Pool síncrono aberto (min=%d max=%d)", min_size, max_size)


async def init_async_pool() -> None:
    global _async_pool
    if _async_pool is not None or _database_url is None:
        return
    min_size, max_size = _pool_bounds()
    kwargs = dict(
        min_size=min_size,
        max_size=max_size,
        timeout=30,
        max_idle=300,
        name="finance_async_pool",
    )
    try:
        _async_pool = AsyncConnectionPool(_database_url, open=False, **kwargs)
        await _async_pool.open(wait=True, timeout=10)
    except TypeError:
        _async_pool = AsyncConnectionPool(_database_url, **kwargs)
        await _async_pool.wait(timeout=10)
    logger.info("Pool assíncrono aberto (min=%d max=%d)", min_size, max_size)


async def close_pools() -> None:
    global _sync_pool, _async_pool
    if _async_pool is not None:
        try:
            await _async_pool.close()
        except Exception:
            logger.exception("Erro fechando pool assíncrono")
        _async_pool = None
    if _sync_pool is not None:
        try:
            _sync_pool.close()
        except Exception:
            logger.exception("Erro fechando pool síncrono")
        _sync_pool = None

 # Obtém conexão síncrona do pool
@contextmanager
def sync_connection() -> Iterator[psycopg.Connection]:
    if _sync_pool is None:
        if _database_url is None:
            raise RuntimeError("DB não inicializado: chame init_db() antes.")
        with psycopg.connect(_database_url) as conn:
            yield conn
        return
    with _sync_pool.connection() as conn:
        yield conn


@asynccontextmanager
async def async_connection() -> AsyncIterator[psycopg.AsyncConnection]:
    if _async_pool is None:
        if _database_url is None:
            raise RuntimeError("DB não inicializado: chame init_db() antes.")
        async with await psycopg.AsyncConnection.connect(_database_url) as aconn:
            yield aconn
        return
    async with _async_pool.connection() as aconn:
        yield aconn
