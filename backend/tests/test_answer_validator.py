from __future__ import annotations

from app.services.answer_validator import validate_answer


class TestValidateAnswer:
    def test_sem_ids_retorna_grounding_vazio(self):
        text = "A receita total é de R$ 50.000,00."
        sanitized, report = validate_answer(text, set())
        assert sanitized == text
        assert report.is_grounded
        assert report.cited == []

    def test_id_verificado_mantido(self):
        text = "A transação txn_001 está paga."
        sanitized, report = validate_answer(text, {"txn_001"})
        assert "txn_001" in sanitized
        assert "txn_001" in report.verified
        assert report.is_grounded

    def test_id_nao_verificado_substituido(self):
        text = "A transação txn_999 é suspeita."
        sanitized, report = validate_answer(text, {"txn_001"})
        assert "txn_999" not in sanitized
        assert "[ID não verificado]" in sanitized
        assert "txn_999" in report.unverified
        assert not report.is_grounded

    def test_mixed_ids(self):
        text = "txn_001 está ok, mas txn_999 precisa atenção."
        known = {"txn_001"}
        sanitized, report = validate_answer(text, known)
        assert "txn_001" in sanitized
        assert "txn_999" not in sanitized
        assert len(report.verified) == 1
        assert len(report.unverified) == 1

    def test_ids_conhecidos_formato_arbitrario(self):
        text = "O contrato ABC-12345 está atrasado."
        known = {"ABC-12345"}
        sanitized, report = validate_answer(text, known)
        assert "ABC-12345" in sanitized
        assert "ABC-12345" in report.verified

    def test_texto_vazio(self):
        sanitized, report = validate_answer("", set())
        assert sanitized == ""
        assert report.is_grounded
