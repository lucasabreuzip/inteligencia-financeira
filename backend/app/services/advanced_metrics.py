"""
Métricas avançadas para gerar insights sobre:
Fluxo de caixa
Padrões de inadimplência
Comportamento de clientes
Anomalias (outliers por z-score, meses fora do padrão)
"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from app.core.constants import INADIMPLENCIA_STATUSES


def _safe_pct(n: float, d: float) -> float:
    return float(n / d) if d else 0.0

    # Divisão vetorizada segura: retorna 0.0 onde denominador == 0
def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return np.where(denominator != 0, numerator / denominator, 0.0)

    # Variação mês a mês da receita paga + aceleração (2ª derivada)
def cashflow_trend(df: pd.DataFrame) -> dict:
    pagos = df[df["status"] == "pago"].copy()
    if pagos.empty:
        return {"meses_analisados": 0}

    pagos["mes"] = pagos["data"].dt.to_period("M").astype(str)
    mensal = pagos.groupby("mes")["valor"].sum().sort_index()
    if len(mensal) < 2:
        return {"meses_analisados": int(len(mensal))}

    var_mm = mensal.pct_change().dropna()
    media_var = float(var_mm.mean())
    ultima_var = float(var_mm.iloc[-1])
    aceleracao = float(var_mm.diff().iloc[-1]) if len(var_mm) >= 2 else 0.0

    maior_queda = var_mm.min()
    pior_mes = str(var_mm.idxmin())
    maior_alta = var_mm.max()
    melhor_mes = str(var_mm.idxmax())

    serie_mensal = [
        {
            "mes": str(mes),
            "receita": round(float(mensal.loc[mes]), 2),
            "variacao_mm": round(float(var_mm.loc[mes]), 4) if mes in var_mm.index else 0.0,
        }
        for mes in mensal.index
    ]

    return {
        "meses_analisados": int(len(mensal)),
        "variacao_media_mm": round(media_var, 4),
        "variacao_ultimo_mes": round(ultima_var, 4),
        "aceleracao_ultimo_mes": round(aceleracao, 4),
        "maior_queda_mm": {"mes": pior_mes, "variacao": round(float(maior_queda), 4)},
        "maior_alta_mm": {"mes": melhor_mes, "variacao": round(float(maior_alta), 4)},
        "receita_ultimo_mes": round(float(mensal.iloc[-1]), 2),
        "receita_mes_anterior": round(float(mensal.iloc[-2]), 2),
        "serie_mensal": serie_mensal,
    }

    # Top N clientes com maior valor e maior taxa de inadimplência (ponderada)
def inadimplencia_por_cliente(df: pd.DataFrame, top: int = 5) -> list[dict]:
    base = df[df["status"] != "cancelado"]
    if base.empty:
        return []

    total_por_cliente = base.groupby("cliente")["valor"].sum()
    inad = base[base["status"].isin(INADIMPLENCIA_STATUSES)]
    inad_por_cliente = inad.groupby("cliente")["valor"].sum()
    qtd_inad = inad.groupby("cliente")["id"].count()

    merged = (
        pd.concat(
            [
                total_por_cliente.rename("total"),
                inad_por_cliente.rename("inad_valor").fillna(0),
                qtd_inad.rename("inad_qtd").fillna(0),
            ],
            axis=1,
        )
        .fillna(0)
        .reset_index()
    )
    merged["taxa"] = _safe_div(merged["inad_valor"], merged["total"])
    # Priorizar clientes relevantes (total alto) com taxa alta
    merged["score_risco"] = merged["inad_valor"] * merged["taxa"]
    merged = merged.sort_values("score_risco", ascending=False).head(top)

    result = merged[["cliente", "total", "inad_valor", "inad_qtd", "taxa"]].copy()
    result.columns = ["cliente", "total_carteira", "inad_valor", "inad_qtd", "taxa_inad"]
    result["total_carteira"] = result["total_carteira"].round(2)
    result["inad_valor"] = result["inad_valor"].round(2)
    result["inad_qtd"] = result["inad_qtd"].astype(int)
    result["taxa_inad"] = result["taxa_inad"].round(4)
    result["cliente"] = result["cliente"].astype(str)
    return result.to_dict(orient="records")


def inadimplencia_por_categoria(df: pd.DataFrame) -> list[dict]:
    if "categoria" not in df.columns:
        return []
    base = df[df["status"] != "cancelado"]
    if base.empty:
        return []
    total = base.groupby("categoria")["valor"].sum()
    inad = base[base["status"].isin(INADIMPLENCIA_STATUSES)]
    inad_val = inad.groupby("categoria")["valor"].sum()

    merged = pd.concat(
        [total.rename("total"), inad_val.rename("inad").fillna(0)], axis=1
    ).fillna(0)
    merged["taxa"] = _safe_div(merged["inad"], merged["total"])
    merged = merged.sort_values("taxa", ascending=False)
    result = merged.reset_index().rename(columns={"categoria": "categoria", "taxa": "taxa_inad"})
    result["total"] = result["total"].round(2)
    result["inad"] = result["inad"].round(2)
    result["taxa_inad"] = result["taxa_inad"].round(4)
    result["categoria"] = result["categoria"].astype(str)
    return result[["categoria", "total", "inad", "taxa_inad"]].to_dict(orient="records")


def inadimplencia_mensal(df: pd.DataFrame) -> list[dict]:
    base = df[df["status"] != "cancelado"].copy()
    if base.empty:
        return []
    base["mes"] = base["data"].dt.to_period("M").astype(str)
    total = base.groupby("mes")["valor"].sum()
    inad = base[base["status"].isin(INADIMPLENCIA_STATUSES)].groupby("mes")["valor"].sum()
    merged = pd.concat([total.rename("total"), inad.rename("inad").fillna(0)], axis=1).fillna(0)
    merged["taxa"] = _safe_div(merged["inad"], merged["total"])
    merged = merged.sort_index()
    result = merged.reset_index().rename(columns={"mes": "mes", "inad": "inad_valor"})
    result["taxa"] = result["taxa"].round(4)
    result["inad_valor"] = result["inad_valor"].round(2)
    result["mes"] = result["mes"].astype(str)
    return result[["mes", "taxa", "inad_valor"]].to_dict(orient="records")

    #HHI + % de receita dos top 3/10 clientes (risco de concentração)
def concentracao_clientes(df: pd.DataFrame) -> dict:
    pagos = df[df["status"] == "pago"]
    if pagos.empty:
        return {}
    por_cliente = pagos.groupby("cliente")["valor"].sum().sort_values(ascending=False)
    total = float(por_cliente.sum())
    if total == 0:
        return {}
    share = por_cliente / total
    hhi = float((share ** 2).sum())  # 0..1; > 0.25 = alta concentração
    return {
        "num_clientes": int(len(por_cliente)),
        "hhi": round(hhi, 4),
        "top3_share": round(float(share.head(3).sum()), 4),
        "top10_share": round(float(share.head(10).sum()), 4),
        "maior_cliente_share": round(float(share.iloc[0]), 4),
        "maior_cliente": str(por_cliente.index[0]),
    }

    # Clientes ativos no último mês x penúltimo (proxy de churn/retenção)
def churn_clientes(df: pd.DataFrame) -> dict:
    base = df[df["status"] != "cancelado"].copy()
    if base.empty:
        return {}
    base["mes"] = base["data"].dt.to_period("M").astype(str)
    meses = sorted(base["mes"].unique())
    if len(meses) < 2:
        return {}
    ultimo, penultimo = meses[-1], meses[-2]
    clientes_ultimo = set(base.loc[base["mes"] == ultimo, "cliente"].unique())
    clientes_penult = set(base.loc[base["mes"] == penultimo, "cliente"].unique())
    perdidos = clientes_penult - clientes_ultimo
    novos = clientes_ultimo - clientes_penult
    retidos = clientes_ultimo & clientes_penult
    return {
        "mes_referencia": ultimo,
        "mes_anterior": penultimo,
        "clientes_ativos": len(clientes_ultimo),
        "clientes_retidos": len(retidos),
        "clientes_novos": len(novos),
        "clientes_perdidos": len(perdidos),
        "taxa_retencao": round(
            _safe_pct(len(retidos), len(clientes_penult) or 1), 4
        ),
        "exemplos_perdidos": sorted(perdidos)[:5],
    }

    # Transações cujo valor está acima de z_thresh desvios-padrão da média
def outliers_transacoes(df: pd.DataFrame, z_thresh: float = 3.0) -> list[dict]:
    base = df[df["status"] != "cancelado"]
    if len(base) < 30:
        return []
    valores = base["valor"]
    mu = float(valores.mean())
    sigma = float(valores.std(ddof=0))
    if sigma == 0:
        return []
    z = (valores - mu) / sigma
    out = base.assign(z=z)
    out = out[out["z"].abs() >= z_thresh].sort_values("z", ascending=False).head(5)
    result = out[["id", "cliente", "valor", "data", "z", "status"]].copy()
    result["id"] = result["id"].astype(str)
    result["cliente"] = result["cliente"].astype(str)
    result["valor"] = result["valor"].round(2)
    result["data"] = result["data"].apply(
        lambda d: d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
    )
    result["z_score"] = result["z"].round(2)
    result["status"] = result["status"].astype(str)
    return result[["id", "cliente", "valor", "data", "z_score", "status"]].to_dict(orient="records")

    # Days Sales Outstanding aproximado: idade média das transações pendentes/atrasadas
def dso_pendentes(df: pd.DataFrame, ref_date: datetime | None = None) -> dict:
    base = df[df["status"].isin(INADIMPLENCIA_STATUSES)]
    if base.empty:
        return {"qtd": 0, "dso_dias": 0, "valor_total": 0.0}
    ref = pd.Timestamp(ref_date) if ref_date else df["data"].max()
    idade = (ref - base["data"]).dt.days
    return {
        "qtd": int(len(base)),
        "dso_dias": int(idade.mean()),
        "dso_maximo_dias": int(idade.max()),
        "valor_total": round(float(base["valor"].sum()), 2),
    }

    # Perfil comportamental por cliente - volume total, realizado, pontualidade, recência.
def comportamento_clientes(df: pd.DataFrame, top: int = 12) -> list[dict]:
    base = df[df["status"] != "cancelado"]
    if base.empty:
        return []

    ref_date = df["data"].max()

    grouped = base.groupby("cliente")
    qtd = grouped["id"].count()
    receita_total = grouped["valor"].sum()
    pagas = base[base["status"] == "pago"].groupby("cliente")
    receita_paga = pagas["valor"].sum()
    qtd_pagas = pagas["id"].count()
    ticket_geral = grouped["valor"].mean()
    ultima_data = grouped["data"].max()

    merged = pd.concat(
        [
            qtd.rename("qtd_transacoes"),
            receita_total.rename("receita_total"),
            receita_paga.rename("receita_paga").fillna(0),
            qtd_pagas.rename("qtd_pagas").fillna(0),
            ticket_geral.rename("ticket_medio"),
            ultima_data.rename("ultima"),
        ],
        axis=1,
    ).fillna({"receita_paga": 0, "qtd_pagas": 0})

    merged["receita_em_aberto"] = (merged["receita_total"] - merged["receita_paga"]).clip(lower=0)
    merged["taxa_pontualidade"] = _safe_div(merged["qtd_pagas"], merged["qtd_transacoes"])
    merged["recencia_dias"] = (ref_date - merged["ultima"]).dt.days

    merged = merged.sort_values("receita_total", ascending=False).head(top)

    result = merged.reset_index()[
        ["cliente", "qtd_transacoes", "receita_total", "receita_paga",
         "receita_em_aberto", "ticket_medio", "taxa_pontualidade", "recencia_dias"]
    ].copy()
    result["cliente"] = result["cliente"].astype(str)
    result["qtd_transacoes"] = result["qtd_transacoes"].astype(int)
    result["receita_total"] = result["receita_total"].round(2)
    result["receita_paga"] = result["receita_paga"].round(2)
    result["receita_em_aberto"] = result["receita_em_aberto"].round(2)
    result["ticket_medio"] = result["ticket_medio"].round(2)
    result["taxa_pontualidade"] = result["taxa_pontualidade"].round(4)
    result["recencia_dias"] = result["recencia_dias"].astype(int)
    return result.to_dict(orient="records")

    # Consolida todas as métricas avançadas para o LLM
def build_advanced_metrics(df: pd.DataFrame) -> dict:
    return {
        "fluxo_caixa": cashflow_trend(df),
        "inadimplencia_mensal": inadimplencia_mensal(df),
        "inadimplencia_por_cliente_top5": inadimplencia_por_cliente(df, top=5),
        "inadimplencia_por_categoria": inadimplencia_por_categoria(df),
        "concentracao_clientes": concentracao_clientes(df),
        "churn_retencao": churn_clientes(df),
        "outliers_valor": outliers_transacoes(df),
        "dso_pendentes": dso_pendentes(df),
        "comportamento_clientes": comportamento_clientes(df),
    }
