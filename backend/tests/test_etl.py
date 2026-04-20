from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pandas as pd
import pytest

from app.services.etl import ETLError, _clean_status_series, _clean_valor_series, _drop_last_month, load_and_clean_csv

class TestCleanValorSeries:
    def test_formato_br_com_virgula(self):
        s = pd.Series(["R$ 1.234,56", "2.000,00", "500,99"])
        result = _clean_valor_series(s)
        assert result.tolist() == pytest.approx([1234.56, 2000.0, 500.99])

    def test_formato_us_com_ponto(self):
        s = pd.Series(["1234.56", "2000.00", "500.99"])
        result = _clean_valor_series(s)
        assert result.tolist() == pytest.approx([1234.56, 2000.0, 500.99])

    def test_float_nativo(self):
        s = pd.Series([1234.56, 2000.0, 500.99])
        result = _clean_valor_series(s)
        assert result.tolist() == pytest.approx([1234.56, 2000.0, 500.99])

    def test_valor_invalido_levanta_etl_error(self):
        s = pd.Series(["abc", "1234.56"])
        with pytest.raises(ETLError, match="Valores numéricos inválidos"):
            _clean_valor_series(s)


    def test_formatos_mistos_na_mesma_coluna(self):
        s = pd.Series(["1.234,56", "1234.56", "1,234.56", "2.000"])
        result = _clean_valor_series(s)
        assert result.tolist() == pytest.approx([1234.56, 1234.56, 1234.56, 2000.0])


# ---- _clean_status_series ----

class TestCleanStatusSeries:
    def test_aliases_pago(self):
        s = pd.Series(["Pago", "paid", "LIQUIDADO"])
        result = _clean_status_series(s)
        assert result.tolist() == ["pago", "pago", "pago"]

    def test_aliases_pendente(self):
        s = pd.Series(["Pendente", "pending", "em aberto", "aberto"])
        result = _clean_status_series(s)
        assert all(v == "pendente" for v in result)

    def test_aliases_atrasado(self):
        s = pd.Series(["Atrasado", "overdue", "vencido"])
        result = _clean_status_series(s)
        assert all(v == "atrasado" for v in result)

    def test_aliases_cancelado(self):
        s = pd.Series(["cancelado", "canceled", "cancelled"])
        result = _clean_status_series(s)
        assert all(v == "cancelado" for v in result)

    def test_status_invalido_levanta_error(self):
        s = pd.Series(["pago", "inexistente"])
        with pytest.raises(ETLError, match="Status inválido"):
            _clean_status_series(s)


# ---- _drop_last_month ----

class TestDropLastMonth:
    def test_sem_dados(self):
        df = pd.DataFrame({"data": pd.Series([], dtype="datetime64[ns]")})
        result = _drop_last_month(df)
        assert result.empty

    def test_um_mes_mantem_tudo(self):
        df = pd.DataFrame({
            "data": pd.to_datetime(["2025-03-01", "2025-03-15"]),
            "id": ["a", "b"],
        })
        result = _drop_last_month(df)
        assert len(result) == 2

    def test_dois_meses_descarta_ultimo(self):
        df = pd.DataFrame({
            "data": pd.to_datetime(["2025-01-15", "2025-02-10", "2025-02-20"]),
            "id": ["a", "b", "c"],
        })
        result = _drop_last_month(df)
        assert len(result) == 1
        assert result.iloc[0]["id"] == "a"


# ---- load_and_clean_csv (integração leve com CSV real) ----

class TestLoadAndCleanCsv:
    def test_csv_valido(self, tmp_path: Path):
        csv_content = dedent("""\
            id;valor;data;status;cliente;descricao
            txn_001;1.500,00;2025-01-15;pago;Cliente A;Contratação de serviço
            txn_002;2.000,00;2025-01-20;pendente;Cliente B;Renovação de contrato
        """)
        f = tmp_path / "test.csv"
        f.write_text(csv_content, encoding="utf-8-sig")
        df = load_and_clean_csv(f)
        assert len(df) == 2
        assert "categoria" in df.columns
        assert df["valor"].dtype == float

    def test_coluna_faltando_levanta_error(self, tmp_path: Path):
        csv_content = "id;valor;data\ntxn_001;100;2025-01-01\n"
        f = tmp_path / "bad.csv"
        f.write_text(csv_content, encoding="utf-8")
        with pytest.raises(ETLError, match="Colunas obrigatórias ausentes"):
            load_and_clean_csv(f)

    def test_ids_duplicados_levanta_error(self, tmp_path: Path):
        csv_content = dedent("""\
            id;valor;data;status;cliente;descricao
            txn_001;100,00;2025-01-15;pago;A;desc
            txn_001;200,00;2025-01-16;pago;B;desc2
        """)
        f = tmp_path / "dup.csv"
        f.write_text(csv_content, encoding="utf-8")
        with pytest.raises(ETLError, match="IDs duplicados"):
            load_and_clean_csv(f)

    def test_extensao_invalida(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("data")
        with pytest.raises(ETLError, match="Extensão não suportada"):
            load_and_clean_csv(f)

    def test_datas_invalidas_levanta_error(self, tmp_path: Path):
        csv_content = dedent("""\
            id;valor;data;status;cliente;descricao
            txn_001;100,00;data-invalida;pago;A;desc
        """)
        f = tmp_path / "bad_date.csv"
        f.write_text(csv_content, encoding="utf-8")
        with pytest.raises(ETLError, match="Datas inválidas"):
            load_and_clean_csv(f)
