from __future__ import annotations

import pandas as pd
import pytest

from app.services.analytics import compute_kpis, compute_monthly_timeseries


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "id": ["t1", "t2", "t3", "t4", "t5"],
        "valor": [1000.0, 2000.0, 500.0, 1500.0, 800.0],
        "data": pd.to_datetime([
            "2025-01-15", "2025-01-20", "2025-02-10",
            "2025-02-15", "2025-03-01",
        ]),
        "status": ["pago", "pendente", "pago", "atrasado", "cancelado"],
        "cliente": ["A", "B", "A", "C", "D"],
        "descricao": ["d1", "d2", "d3", "d4", "d5"],
        "categoria": ["contratacao", "renovacao", "suporte", "consultoria", "outros"],
    })


class TestComputeKpis:
    def test_receita_total_somente_pagos(self):
        df = _sample_df()
        kpis = compute_kpis(df)
        # pagos: t1=1000 + t3=500 = 1500
        assert kpis["receita_total"] == 1500.0

    def test_total_exclui_cancelados(self):
        df = _sample_df()
        kpis = compute_kpis(df)
        # cancelado=t5 excluído, sobram 4
        assert kpis["total_transacoes"] == 4

    def test_taxa_inadimplencia(self):
        df = _sample_df()
        kpis = compute_kpis(df)
        # inadimplentes: t2=2000 + t4=1500 = 3500
        # total bruto (sem cancelado): 1000+2000+500+1500 = 5000
        assert kpis["taxa_inadimplencia"] == pytest.approx(3500 / 5000, rel=1e-3)

    def test_ticket_medio(self):
        df = _sample_df()
        kpis = compute_kpis(df)
        # considerado (sem cancelado): [1000, 2000, 500, 1500], média=1250
        assert kpis["ticket_medio"] == pytest.approx(1250.0, rel=1e-3)

    def test_periodo(self):
        df = _sample_df()
        kpis = compute_kpis(df)
        assert kpis["periodo_inicio"] == "2025-01-15"
        assert kpis["periodo_fim"] == "2025-03-01"


class TestComputeMonthlyTimeseries:
    def test_retorna_meses_ordenados(self):
        df = _sample_df()
        ts = compute_monthly_timeseries(df)
        periodos = [t[0] for t in ts]
        assert periodos == sorted(periodos)

    def test_receita_somente_pagos(self):
        df = _sample_df()
        ts = compute_monthly_timeseries(df)
        # Jan: t1 pago 1000
        jan = [t for t in ts if "2025-01" in t[0]][0]
        assert jan[1] == 1000.0

    def test_contagem_inclui_todos(self):
        df = _sample_df()
        ts = compute_monthly_timeseries(df)
        total_count = sum(t[2] for t in ts)
        assert total_count == len(df)
