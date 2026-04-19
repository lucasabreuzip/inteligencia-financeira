from __future__ import annotations

STATUS_PAGO = "pago"
STATUS_PENDENTE = "pendente"
STATUS_ATRASADO = "atrasado"
STATUS_CANCELADO = "cancelado"

STATUS_INADIMPLENCIA: frozenset[str] = frozenset({STATUS_ATRASADO})

STATUS_EM_ABERTO: frozenset[str] = frozenset({STATUS_PENDENTE, STATUS_ATRASADO})

STATUS_VALIDOS: frozenset[str] = frozenset(
    {STATUS_PAGO, STATUS_PENDENTE, STATUS_ATRASADO, STATUS_CANCELADO}
)