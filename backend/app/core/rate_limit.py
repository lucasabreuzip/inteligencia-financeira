"""
Rate limiting por IP via slowapi.

Uso:
  - Registre o middleware em main.py (app.state.limiter = limiter + exception handler).
  - Decore endpoints com @limiter.limit(settings.chat_rate_limit), passando `request: Request`.

Motivo: /api/chat dispara tool calls na OpenAI. Sem limite, um visitante pode
drenar o budget da conta.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
