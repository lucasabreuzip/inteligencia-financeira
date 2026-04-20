"""Constantes compartilhadas entre modulos.

Valores que sao invariantes de negocio (nao configuraveis por ambiente) vivem
aqui; o que varia por deploy fica em `core/config.py` (Settings).
"""
from __future__ import annotations

# Agent (chat): loop de tool-calls e timeouts.
MAX_AGENT_ITERATIONS = 5
CHAT_TIMEOUT_SEC = 90

# Historico conversacional. 20 mensagens = ~10 turnos (user+assistant).
MAX_HISTORY_MESSAGES = 20
# Cap por mensagem no prompt — evita estourar contexto com turnos gigantes.
MAX_HISTORY_MSG_CHARS = 4000

# Status que contam como inadimplencia nos agregados financeiros.
INADIMPLENCIA_STATUSES: frozenset[str] = frozenset({"pendente", "atrasado"})
