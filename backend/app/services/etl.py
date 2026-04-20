from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from app.services.categorizer import categorize_dataframe

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["id", "valor", "data", "status", "cliente", "descricao"]
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


class ETLError(ValueError):
    pass

    #Normaliza um valor monetario textual sem assumir um formato global
def _normalize_numeric_token(value: object) -> str:
    s = str(value).strip()
    if not s:
        return s

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    s = s.replace("\u00a0", "")
    s = s.replace("R$", "").replace("$", "")
    s = "".join(s.split())
    if s.startswith("-"):
        negative = True
        s = s[1:]

    last_dot = s.rfind(".")
    last_comma = s.rfind(",")

    if last_dot != -1 and last_comma != -1:
        if last_comma > last_dot:
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif last_comma != -1:
        integer, fractional = s.rsplit(",", 1)
        if 1 <= len(fractional) <= 2:
            s = f"{integer.replace(',', '')}.{fractional}"
        else:
            s = s.replace(",", "")
    elif last_dot != -1:
        integer, fractional = s.rsplit(".", 1)
        if 1 <= len(fractional) <= 2:
            s = f"{integer}.{fractional}"
        else:
            s = s.replace(".", "")

    if negative and s:
        s = f"-{s}"
    return s


def _clean_valor_series(series: pd.Series) -> pd.Series:
    """Suporta numeros BR/US misturados na mesma coluna e floats nativos."""
    if pd.api.types.is_numeric_dtype(series):
        return series.astype(float)

    normalized = series.map(_normalize_numeric_token)
    numeric = pd.to_numeric(normalized, errors="coerce")
    if numeric.isna().any():
        bad = series[numeric.isna()].head(3).tolist()
        raise ETLError(f"Valores numéricos inválidos na coluna 'valor': {bad}")
    return numeric.astype(float)


STATUS_ALIASES = {
    "pago": "pago",
    "paid": "pago",
    "liquidado": "pago",
    "pendente": "pendente",
    "pending": "pendente",
    "em aberto": "pendente",
    "aberto": "pendente",
    "atrasado": "atrasado",
    "overdue": "atrasado",
    "vencido": "atrasado",
    "cancelado": "cancelado",
    "canceled": "cancelado",
    "cancelled": "cancelado",
}


def _clean_status_series(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip().str.lower()
    mapped = s.map(STATUS_ALIASES)
    invalid_mask = mapped.isna()
    if invalid_mask.any():
        invalid = sorted(set(s[invalid_mask].unique()))
        raise ETLError(
            f"Status inválido(s): {invalid}. Esperado: {sorted(set(STATUS_ALIASES.values()))}"
        )
    return mapped


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)
    except UnicodeDecodeError:
        return pd.read_csv(path, sep=";", encoding="latin-1", dtype=str)


def _read_xlsx(path: Path) -> pd.DataFrame:
    """Lê XLSX deixando Pandas inferir tipos. ETL posterior é tipo-agnóstico."""
    return pd.read_excel(path, engine="openpyxl")


def load_and_clean_csv(path: Path) -> pd.DataFrame:
    """
    Lê CSV (delimitador `;`, decimal `,`) ou XLSX e devolve DataFrame padronizado:
      - valor: float
      - data:  datetime64 dia
      - status: categoria lower-case (pago | pendente | atrasado | cancelado)
      - categoria: string derivada da descrição via regras
      - id, cliente, descricao: strings trimadas
    """
    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ETLError(f"Extensão não suportada: {ext}. Use .csv ou .xlsx.")
    df = _read_xlsx(path) if ext in {".xlsx", ".xls"} else _read_csv(path)

    df.columns = [c.strip().lower() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ETLError(f"Colunas obrigatórias ausentes: {missing}")

    df = df[REQUIRED_COLUMNS].copy()
    df["id"] = df["id"].astype(str).str.strip()
    df["cliente"] = df["cliente"].astype(str).str.strip()
    df["descricao"] = df["descricao"].astype(str).str.strip()

    df["valor"] = _clean_valor_series(df["valor"])
    df["status"] = _clean_status_series(df["status"])

    df["data"] = pd.to_datetime(df["data"], errors="coerce", format="mixed", dayfirst=False)
    if df["data"].isna().any():
        bad = df.loc[df["data"].isna(), "id"].head(3).tolist()
        raise ETLError(f"Datas inválidas em transações: {bad}")
    df["data"] = df["data"].dt.normalize()

    if df["id"].duplicated().any():
        dups = df.loc[df["id"].duplicated(), "id"].head(3).tolist()
        raise ETLError(f"IDs duplicados encontrados: {dups}")

    if df.empty:
        raise ETLError("Arquivo não contém linhas de dados.")

    df = _drop_last_month(df)

    if df.empty:
        raise ETLError("Após descartar o último mês (parcial), não restaram linhas.")

    df["categoria"] = categorize_dataframe(df, source_column="descricao")

    return df.reset_index(drop=True)

 # mes com variacao causa ruidos
def _drop_last_month(df: pd.DataFrame) -> pd.DataFrame:
    """
    Descarta o mês mais recente do dataset - esse mês costuma estar parcial
    (mês corrente ou corte de exportação), distorcendo M/M e tendências.
    Mantém o comportamento idempotente: se só houver 1 mês, mantém tudo.
    """
    if df.empty:
        return df
    periodos = df["data"].dt.to_period("M")
    unicos = periodos.unique()
    if len(unicos) <= 1:
        return df
    ultimo = periodos.max()
    antes = len(df)
    df_filtrado = df.loc[periodos != ultimo].copy()
    logger.info(
        "ETL: descartado último mês %s (%d de %d linhas removidas).",
        ultimo,
        antes - len(df_filtrado),
        antes,
    )
    return df_filtrado
