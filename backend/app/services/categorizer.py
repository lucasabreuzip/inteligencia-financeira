from __future__ import annotations

import re

import pandas as pd

CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("contratacao", [r"\bcontrata[cç][aã]o", r"\baquisi", r"\bnova\s+contrata"]),
    ("renovacao", [r"\brenova"]),
    ("assinatura", [r"\bassinatura", r"\bplano\s+premium", r"\bmensal"]),
    ("servicos_recorrentes", [r"recorrente", r"ciclo contratado"]),
    ("infraestrutura", [r"infraestrutura", r"servidor", r"integra[cç][aã]o"]),
    ("suporte", [r"\bsuporte", r"atendimento"]),
    ("manutencao", [r"manuten[cç][aã]o", r"monitoramento", r"atualiza[cç]"]),
    ("consultoria", [r"consultoria", r"treinamento", r"workshop"]),
    ("licenciamento", [r"licen[cç]a", r"acesso à plataforma", r"acesso a plataforma"]),
    ("cobranca", [r"cobran[cç]a", r"fatura"]),
]

COMPILED_RULES: list[tuple[str, list[re.Pattern[str]]]] = [
    (cat, [re.compile(p, re.IGNORECASE) for p in patterns])
    for cat, patterns in CATEGORY_RULES
]

DEFAULT_CATEGORY = "outros"

CATEGORY_LABELS: dict[str, str] = {
    "contratacao": "Contratação",
    "renovacao": "Renovação",
    "assinatura": "Assinatura",
    "servicos_recorrentes": "Serviços recorrentes",
    "infraestrutura": "Infraestrutura",
    "suporte": "Suporte",
    "manutencao": "Manutenção",
    "consultoria": "Consultoria",
    "licenciamento": "Licenciamento",
    "cobranca": "Cobrança",
    "outros": "Outros",
}


def categorize_text(text: str) -> str:
    if not text:
        return DEFAULT_CATEGORY
    for category, patterns in COMPILED_RULES:
        for pat in patterns:
            if pat.search(text):
                return category
    return DEFAULT_CATEGORY


def categorize_dataframe(df: pd.DataFrame, source_column: str = "descricao") -> pd.Series:
    return df[source_column].fillna("").astype(str).map(categorize_text)
