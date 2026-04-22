"""
Prompts e schemas de ferramentas do agente RAG.
system prompt, tool definitions
"""
from __future__ import annotations

from app.services.prompt_safety import PROMPT_INJECTION_GUARD

SYSTEM_PROMPT = (
    "Você é um 'Consultor Financeiro de Elite' analisando a base de transações "
    "do usuário usando EXCLUSIVAMENTE as ferramentas disponíveis e o SNAPSHOT GLOBAL.\n\n"
    "REGRA DE OURO — ANTI-ALUCINAÇÃO E PRECISÃO:\n"
    "• Nunca afirme um número, ID, data, cliente ou descrição que não apareça "
    "  literalmente em (a) um resultado de ferramenta ou (b) no SNAPSHOT GLOBAL.\n"
    "• Se não encontrar a informação na base consultada, responda: "
    "  \"Não encontrei essa informação nos dados.\"\n"
    "• Nunca extrapole ou estime. Só relate o que foi efetivamente medido.\n\n"
    "ESTRATÉGIA DE RETRIEVAL E TÁTICA CORPORATIVA:\n"
    "1. TIPO DE PERGUNTA:\n"
    "   a) Visão geral, diagnósticos corporativos, conselhos estratégicos ou evolução temporal \n"
    "      → OBRIGATÓRIO: Chame IMEDIATAMENTE `fetch_ai_diagnostics` E `get_advanced_metrics` juntas. "
    "      Isso lhe dará a visão do Fluxo de Caixa, HHI, Retenção e o Lado Executivo Primário simultaneamente.\n"
    "   b) Análise macro específica (fluxo de caixa, DSO, outliers) sem contexto global "
    "      → get_advanced_metrics.\n"
    "   c) Quantitativa agregada (contagem, totais) "
    "      → count_transactions ou aggregate_transactions.\n"
    "   d) Listagem específica e relatórios → list_transactions.\n"
    "   e) Qualitativa/Contexto (descricao) → semantic_search.\n"
    "   f) Busca de UM OU MAIS IDs específicos → OBRIGATÓRIO: use list_transactions passando o parâmetro `id` exato.\n"
    "2. Se a busca semântica (semantic_search) retornar 'fraca', TENTE list_transactions "
    "   com 'descricao_contains' ou 'categoria'. Nunca desista no primeiro erro.\n"
    "3. Para TOTAIS gerais utilize o SNAPSHOT GLOBAL.\n"
    "4. Ao cruzar sintomas críticos, você deve adotar uma Cadeia de Pensamento (Chain of Thought), "
    "   amarrando os achados do 'fetch_ai_diagnostics' com suas buscas.\n\n"
    "PROIBIDO DIZER O ÓBVIO E EXCELÊNCIA TÁTICA:\n"
    "• As suas respostas devem carregar peso executivo. Ao invés de vomitar dados secos, "
    "  tente ser ultra pragmático e estratégico. Use jargão empresarial correto mas rápido.\n"
    "• Traga visibilidade imediata às dores financeiras.\n\n"
    "FORMATO E ESTÉTICA:\n"
    "1. Você DEVE usar **Markdown** de forma extensiva para criar respostas visualmente arrasadoras.\n"
    "2. Use **Tabelas Markdown** elegantes sempre que o usuário pedir listagens, top clientes ou comparações de múltiplos meses.\n"
    "3. Use **Negrito** nos Nomes de Clientes, Categorias e Valores em R$ ou Porcentagens, para que saltem aos olhos.\n"
    "4. Use Listas enumeradas simples para sumarizar diagnósticos.\n"
    "5. Mantenha os valores em R$ rigorosamente formatados com duas casas decimais e separador brasileiro.\n\n"
    + PROMPT_INJECTION_GUARD
)

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_transactions",
            "description": "Lista transações do job aplicando filtros exatos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "Utilize para buscar exatamente a transação com este ID."},
                    "status": {
                        "type": "string",
                        "enum": ["pago", "pendente", "atrasado", "cancelado"],
                    },
                    "categoria": {
                        "type": "string",
                        "description": "contratacao|renovacao|assinatura|servicos_recorrentes|infraestrutura|suporte|manutencao|consultoria|licenciamento|cobranca|outros",
                    },
                    "cliente_contains": {"type": "string"},
                    "descricao_contains": {"type": "string"},
                    "min_valor": {"type": "number"},
                    "max_valor": {"type": "number"},
                    "data_inicio": {"type": "string", "description": "YYYY-MM-DD"},
                    "data_fim": {"type": "string", "description": "YYYY-MM-DD"},
                    "order_by": {
                        "type": "string",
                        "enum": ["data", "valor", "cliente", "status"],
                    },
                    "order_dir": {"type": "string", "enum": ["asc", "desc"]},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 200},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_transactions",
            "description": "Conta, soma e calcula média de transações com filtros.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pago", "pendente", "atrasado", "cancelado"],
                    },
                    "categoria": {
                        "type": "string",
                        "description": "contratacao|renovacao|assinatura|servicos_recorrentes|infraestrutura|suporte|manutencao|consultoria|licenciamento|cobranca|outros",
                    },
                    "cliente_contains": {"type": "string"},
                    "descricao_contains": {"type": "string"},
                    "min_valor": {"type": "number"},
                    "max_valor": {"type": "number"},
                    "data_inicio": {"type": "string"},
                    "data_fim": {"type": "string"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "aggregate_transactions",
            "description": "Agrupa por status, cliente ou mês com métrica count/sum/avg.",
            "parameters": {
                "type": "object",
                "properties": {
                    "group_by": {"type": "string", "enum": ["status", "cliente", "mes"]},
                    "metric": {"type": "string", "enum": ["count", "sum", "avg"]},
                    "status": {"type": "string"},
                    "categoria": {"type": "string"},
                    "cliente_contains": {"type": "string"},
                    "data_inicio": {"type": "string"},
                    "data_fim": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
                "required": ["group_by", "metric"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_advanced_metrics",
            "description": (
                "Retorna análises evolutivas e estruturais calculadas em Pandas. "
                "USE para perguntas sobre: fluxo de caixa, tendência de receita, "
                "variação mês a mês, aceleração, concentração de clientes (HHI), "
                "DSO/inadimplência por período, churn/retenção, outliers, ranking "
                "de devedores. NÃO use para listar transações — use list_transactions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "section": {
                        "type": "string",
                        "enum": [
                            "all",
                            "fluxo_caixa",
                            "inadimplencia_mensal",
                            "inadimplencia_por_cliente_top5",
                            "inadimplencia_por_categoria",
                            "concentracao_clientes",
                            "retencao_mensal",
                            "churn_real",
                            "outliers_valor",
                            "idade_media_recebiveis",
                            "dso_tradicional",
                        ],
                        "description": "Seção específica para reduzir payload. Default: 'all'.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_ai_diagnostics",
            "description": (
                "Busca o diagnóstico oficial previamente computado pela plataforma. "
                "Retorna a classificação geral, o resumo executivo e os 3 alertas críticos da empresa. "
                "Use esta ferramenta sempre que for indagado sobre a 'situação da empresa', "
                "'o que você acha da base', ou pedir conselhos estratégicos globais."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "semantic_search",
            "description": (
                "Busca por similaridade semântica nas descrições das transações. "
                "Use para perguntas qualitativas. Retorna qualidade_relevancia para "
                "você avaliar se deve combinar com list_transactions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta em linguagem natural"},
                    "k": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
                    "categoria": {
                        "type": "string",
                        "description": "Escopar busca a uma categoria específica (ex.: contratacao, assinatura)",
                    },
                    "relevance_threshold": {
                        "type": "number",
                        "description": "Distância máxima PGVector (<=>). Default 1.6 para embeddings robustos.",
                        "default": 1.6,
                    },
                },
                "required": ["query"],
            },
        },
    },
]
