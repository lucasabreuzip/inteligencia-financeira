"""Persistencia de historico de chat.
"""
from __future__ import annotations

import logging

from psycopg.rows import dict_row

from app.core.constants import MAX_HISTORY_MESSAGES
from app.infrastructure.db import async_connection

logger = logging.getLogger(__name__)

    # Retorna as ultimas mensagens da sessao em ordem cronologica crescente
async def load_history(job_id: str, session_id: str) -> list[dict]:
    async with async_connection() as aconn:
        async with aconn.cursor(row_factory=dict_row) as cur:
            # Pega as N ultimas (DESC + LIMIT) e inverte para cronologico.
            await cur.execute(
                """
                SELECT role, content
                FROM (
                    SELECT id, role, content
                    FROM chat_messages
                    WHERE job_id = %s AND session_id = %s
                    ORDER BY id DESC
                    LIMIT %s
                ) AS recentes
                ORDER BY id ASC
                """,
                (job_id, session_id, MAX_HISTORY_MESSAGES),
            )
            return await cur.fetchall()

    # Grava par (pergunta, resposta) numa unica transacao.
async def append_exchange(
    job_id: str, session_id: str, user_question: str, assistant_answer: str
) -> None:

    try:
        async with async_connection() as aconn:
            async with aconn.cursor() as cur:
                await cur.executemany(
                    """
                    INSERT INTO chat_messages (job_id, session_id, role, content)
                    VALUES (%s, %s, %s, %s)
                    """,
                    [
                        (job_id, session_id, "user", user_question),
                        (job_id, session_id, "assistant", assistant_answer),
                    ],
                )
                await aconn.commit()
    except Exception:
        logger.exception(
            "Falha ao persistir chat job=%s session=%s — conversa nao salva",
            job_id, session_id,
        )
