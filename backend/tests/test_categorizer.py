from __future__ import annotations

from app.services.categorizer import categorize_text, DEFAULT_CATEGORY


class TestCategorizeText:
    def test_contratacao(self):
        assert categorize_text("Contratação de novo serviço") == "contratacao"
        assert categorize_text("Aquisição de licença") == "contratacao"

    def test_renovacao(self):
        assert categorize_text("Renovação anual do contrato") == "renovacao"

    def test_assinatura(self):
        assert categorize_text("Assinatura mensal premium") == "assinatura"
        assert categorize_text("Plano premium empresarial") == "assinatura"

    def test_servicos_recorrentes(self):
        assert categorize_text("Pagamento recorrente do serviço") == "servicos_recorrentes"

    def test_infraestrutura(self):
        assert categorize_text("Hospedagem de servidor") == "infraestrutura"
        assert categorize_text("Integração de sistemas") == "infraestrutura"

    def test_suporte(self):
        assert categorize_text("Suporte técnico avançado") == "suporte"
        assert categorize_text("Atendimento ao cliente") == "suporte"

    def test_manutencao(self):
        assert categorize_text("Manutenção preventiva") == "manutencao"
        assert categorize_text("Monitoramento de rede") == "manutencao"

    def test_consultoria(self):
        assert categorize_text("Consultoria estratégica") == "consultoria"
        assert categorize_text("Workshop de inovação") == "consultoria"

    def test_licenciamento(self):
        assert categorize_text("Licença de uso anual") == "licenciamento"
        assert categorize_text("Acesso à plataforma") == "licenciamento"

    def test_cobranca(self):
        assert categorize_text("Cobrança de fatura") == "cobranca"
        assert categorize_text("Geração de fatura trimestral") == "cobranca"

    def test_outros_quando_sem_match(self):
        assert categorize_text("Pagamento genérico XYZ") == DEFAULT_CATEGORY
        assert categorize_text("") == DEFAULT_CATEGORY

    def test_case_insensitive(self):
        assert categorize_text("RENOVAÇÃO DO CONTRATO") == "renovacao"

    def test_participio_contratado_nao_vira_contratacao(self):
        # Particípios de "contratar" não devem capturar assinaturas/renovações
        # quando o sujeito primário da frase é outro. Só o substantivo
        # "contratação" (ou "aquisição"/"nova contratação") deve disparar.
        assert (
            categorize_text(
                "Pagamento referente à assinatura mensal de serviços digitais "
                "contratados pela empresa"
            )
            == "assinatura"
        )
        assert categorize_text("Serviço contratado previamente") == DEFAULT_CATEGORY
        assert categorize_text("Renovação de pacote contratado") == "renovacao"

    def test_contratacao_substantivo_ainda_casa(self):
        assert categorize_text("Contratação de novo pacote") == "contratacao"
        assert categorize_text("Nova contratação anual") == "contratacao"
        assert categorize_text("Aquisição de módulo extra") == "contratacao"
