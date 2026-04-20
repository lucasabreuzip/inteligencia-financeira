"""
Validador pós-resposta do agente RAG.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Padrões de ID típicos: txn_XXX, TX-123, id-like tokens com prefixo alfabético.
# Usamos match defensivo só para detectar candidatos — a verificação final é
# feita contra o conjunto de IDs conhecidos (ctx.sources).
_TXN_PATTERN = re.compile(r"\btxn[_-][A-Za-z0-9]+\b", re.IGNORECASE)
_GENERIC_ID_PATTERN = re.compile(r"\b[A-Za-z][A-Za-z0-9_-]{3,}\b")

_UNVERIFIED_PLACEHOLDER = "[ID não verificado]"


@dataclass
class GroundingReport:
    cited: list[str] = field(default_factory=list)
    verified: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)

    @property
    def is_grounded(self) -> bool:
        return not self.unverified

    def to_dict(self) -> dict:
        return {
            "cited": self.cited,
            "verified": self.verified,
            "unverified": self.unverified,
            "is_grounded": self.is_grounded,
        }


def _extract_candidates(answer: str, known_ids: set[str]) -> set[str]:
    candidates: set[str] = set()

    for m in _TXN_PATTERN.finditer(answer):
        candidates.add(m.group(0))

    # Match exato de IDs conhecidos (formatos arbitrários vindos de CSV do usuário).
    for kid in known_ids:
        if len(kid) < 3:
            continue
        if re.search(rf"(?<![A-Za-z0-9_-]){re.escape(kid)}(?![A-Za-z0-9_-])", answer):
            candidates.add(kid)

    return candidates


def validate_answer(answer: str, known_ids: set[str]) -> tuple[str, GroundingReport]:

    if not answer:
        return answer, GroundingReport()

    candidates = _extract_candidates(answer, known_ids)
    if not candidates:
        return answer, GroundingReport()

    known_lower = {k.lower() for k in known_ids}
    verified: list[str] = []
    unverified: list[str] = []
    for cand in sorted(candidates):
        if cand in known_ids or cand.lower() in known_lower:
            verified.append(cand)
        elif _TXN_PATTERN.fullmatch(cand):
            unverified.append(cand)

    sanitized = answer
    for bad in unverified:
        sanitized = re.sub(
            rf"(?<![A-Za-z0-9_-]){re.escape(bad)}(?![A-Za-z0-9_-])",
            _UNVERIFIED_PLACEHOLDER,
            sanitized,
        )

    return sanitized, GroundingReport(
        cited=sorted(candidates),
        verified=sorted(verified),
        unverified=sorted(unverified),
    )
