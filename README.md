<div align="center">

# Plataforma de Inteligência Financeira IA

**Transforme planilhas de transações em decisões estratégicas - diagnóstico executivo automático e chat inteligente que conversa com seus dados.**

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-19-000000?logo=nextdotjs)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://postgresql.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?logo=openai)](https://openai.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://docker.com)

</div>

---

Uma plataforma completa que recebe arquivos CSV/XLSX de transações financeiras, processa, analisa e entrega **inteligência acionável em segundos**.

Ao invés de passar horas cruzando planilhas no Excel, o gestor financeiro faz o upload e obtém instantaneamente:

- 📊 **Dashboard executivo** com KPIs, tendências e alertas
- 🤖 **Diagnóstico automático por IA** que classifica a saúde financeira e aponta riscos
- 💬 **Chat inteligente** que responde perguntas em português sobre os dados
- 🔍 **Busca semântica** que encontra transações por significado, não só por filtros

---

## Funcionalidades

### 📥 Ingestão Inteligente
- Upload de CSV e Excel com validação automática
- **ETL robusto**: reconhece formatos numéricos misturados (BR, US, ou ambos na mesma coluna)
- Normalização automática de status, datas e categorias
- Pipeline com 6 fases acompanhadas em tempo real via barra de progresso

### 📊 Dashboard Executivo
- Receita total, ticket médio, taxa de inadimplência, total de transações
- Gráficos de receita ao longo do tempo e fluxo de caixa mensal
- Classificação automática: **Saudável**, **Atenção** ou **Crítico**
- Alertas gerados por IA com severidade e sugestões de ação

### 💬 Chat com Agente Híbrido (SQL + Semântico)
O diferencial da plataforma. O usuário pergunta em português e o agente decide sozinho como responder:

- *"Qual o maior cliente devedor?"* → Consulta SQL agregada
- *"Mostre transações de consultoria acima de R$ 10 mil"* → Listagem filtrada
- *"Tem alguma transação estranha em janeiro?"* → Busca semântica + outliers
- *"Como está o fluxo de caixa?"* → Métricas avançadas (variação mês a mês)

**Respostas em streaming** — o usuário vê o texto sendo digitado em tempo real, com indicação de quais ferramentas foram usadas.

### 🔬 Métricas Avançadas

| Métrica | Para que serve |
|---|---|
| **Fluxo de Caixa** | Variação de receita mês a mês com detecção de aceleração ou queda |
| **DSO** | Prazo médio de recebimento — identifica gargalos de inadimplência |
| **HHI** | Índice de concentração de clientes — risco de depender de poucos |
| **Churn** | Clientes que deixaram de transacionar ao longo do tempo |
| **Outliers** | Transações fora do padrão (possíveis erros ou eventos atípicos) |
| **Inadimplência por Categoria** | Identifica quais serviços geram mais inadimplência |

### 🔐 Segurança e Privacidade
- API key nunca exposta ao navegador (proxy server-side)
- Postgres isolado na rede interna Docker
- SQL 100% parametrizado
- Anti-alucinação: IDs citados pelo IA são validados contra resultados reais
- Mitigação de prompt injection com envelopamento de dados

---

## Como Funciona

<img width="1332" height="456" alt="Fluxoprinceipas3" src="https://github.com/user-attachments/assets/1a77c514-514c-4959-8052-00c245375f86" />

---

## Arquitetura

<img width="1370" height="827" alt="arquitetura_lucasabreu" src="https://media.discordapp.net/attachments/1495950483179966495/1496347604701810839/ArqLucas.png?ex=69e98dcd&is=69e83c4d&hm=eab15b64aecc639a1c473a975199c9afde0992d7d96a76d80c2acf9048e53310&=&format=webp&quality=lossless&width=1844&height=864" />

---

## Tecnologias Escolhidas

| Camada | Tecnologia | Por que foi escolhida |
|---|---|---|
| **Frontend** | Next.js 19 + React 19 | SSR, proxy server-side seguro, streaming nativo |
| **Estilo** | Tailwind CSS | Design system consistente, responsivo, rápido |
| **Gráficos** | Recharts 3.8 | Integração nativa com React 19, visualizações interativas |
| **Backend** | FastAPI + Python 3.12 | Performance, tipagem automática, documentação OpenAPI |
| **Banco** | PostgreSQL 16 + pgvector | Dados relacionais e busca vetorial no mesmo banco - sem JOINs entre stores |
| **Driver DB** | psycopg3 | Pools sync + async, COPY bulk para alta performance |
| **IA/LLM** | OpenAI GPT-4o-mini + embeddings | Custo-benefício, tool-calling nativo, respostas estruturadas em JSON |
| **Infra** | Docker Compose | Um comando sobe toda a stack, ambiente reprodutível |
| **Observabilidade** | Langfuse | Traces, custo por requisição, zero overhead quando desligado |

---

## Instalação Rápida

### Requisitos
- Docker Desktop 24+ (recomendado)
- OU Python 3.12 + Node.js 20 (desenvolvimento local)
- Chave OpenAI (opcional — sem ela, insights usam lógica determinística)

### Docker Compose

```bash
# Clone o repositório
git clone https://github.com/lucasabreuzip/inteligencia-financeira.git
cd inteligencia-financeira

# Copie e configure o ambiente
cp backend/.env.example .env
# Edite .env com suas credenciais

# Suba tudo
docker compose up --build
```

**Pronto!**
- 🌐 Acesse: http://localhost:3001
- 🔧 Health check: http://localhost:8000/api/health

### Smoke Test (2 minutos)

1. Abra http://localhost:3001
2. Arraste o arquivo `dados_financeiros.csv`
3. Acompanhe o progresso em tempo real
4. Explore o dashboard e faça perguntas no chat

---

## Decisões de Engenharia

### 🔒 Segurança em Primeiro Lugar
- **API key isolada no servidor**: o frontend nunca vê a chave de API. Toda comunicação passa por um proxy server-side no Next.js (`app/api/[...path]/route.ts`), eliminando o risco de exposição no bundle JavaScript.
- **SQL 100% parametrizado**: o agente LLM não escreve SQL livre — usa templates parametrizados com whitelist de colunas.
- **Anti-alucinação validada**: toda resposta do LLM passa por um validador que verifica se IDs de transações citados realmente apareceram nos resultados das ferramentas. IDs inventados são sinalizados como `[ID não verificado]`.

### ⚡ Performance e Escalabilidade
- **COPY FROM STDIN**: persistência de milhares de transações via bulk copy, não INSERT row-by-row.
- **Pools duplos de conexão**: sync para workers pesados (ETL, COPY), async para endpoints leves (API).
- **Cache TTL thread-safe**: métricas avançadas são cacheadas por `job_id` — chat multi-turno não recomputa.
- **Semáforo de concorrência**: até 5 pipelines simultâneos, com fila automática para uploads extras.
- **BackgroundTasks nativo**: sem dependência de Celery/Redis para o perfil de carga atual (upgrade path mapeado).

### 🧠 IA com Controle Total
- **Tool-calling nativo OpenAI**, não frameworks de agente. Controle absoluto sobre loop (máx. 5 iterações), logging granular e custo.
- **Documento vetorial otimizado**: embeda apenas `[categoria] descricao`, não metadados estruturais. Busca híbrida em uma única query SQL.
- **Fallback determinístico**: se a OpenAI falhar ou estiver ausente, o pipeline continua com classificação baseada em regras.

### 🧪 Qualidade de Código
- **58 testes em ~1.2s**, sem necessidade de banco real (stubs de `psycopg` via `conftest.py`).
- **Separação estrita de camadas**: `api/` → `services/` → `infrastructure/`. A camada de rotas nunca toca o banco diretamente.

---

## Estrutura do Projeto

```
inteligencia-financeira/
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                          # Entrypoint FastAPI + lifespan
│       │
│       ├── api/                             # 🌐 Camada de rotas (HTTP)
│       │   ├── upload.py                    #   POST /api/upload
│       │   ├── status.py                    #   GET  /api/status/{id} (SSE)
│       │   ├── dashboard.py                 #   GET  /api/dashboard/{id}
│       │   ├── transactions.py              #   GET  /api/transactions/{id}
│       │   ├── insights.py                  #   GET  /api/insights/advanced/{id}
│       │   ├── chat.py                      #   POST /api/chat/stream (SSE)
│       │   └── routers/
│       │       └── health.py                #   GET  /api/health + /api/health/db
│       │
│       ├── core/                            # ⚙️ Configuração e cross-cutting
│       │   ├── config.py                    #   Settings (pydantic-settings)
│       │   ├── constants.py                 #   Constantes de negócio
│       │   ├── auth.py                      #   API key + HMAC compare
│       │   └── rate_limit.py                #   Rate limiting por IP
│       │
│       ├── domain/                          # 📋 Contratos (schemas Pydantic)
│       │   ├── schemas.py                   #   KPIs, Transactions, Jobs
│       │   └── chat_schemas.py              #   ChatRequest, ChatResponse, Grounding
│       │
│       ├── infrastructure/                  # 🗄️ Persistência e I/O
│       │   ├── db.py                        #   Fachada de re-export (compatibilidade)
│       │   ├── pool.py                      #   Pools sync/async + init_db com retry
│       │   ├── schema.py                    #   DDL SQL + migrações idempotentes
│       │   ├── repositories.py              #   CRUD: jobs, KPIs, transactions, timeseries
│       │   └── job_store.py                 #   Estado in-memory + pub/sub de progresso
│       │
│       ├── services/                        # 🧠 Lógica de negócio
│       │   ├── etl.py                       #   Limpeza e normalização de dados
│       │   ├── analytics.py                 #   KPIs e série temporal
│       │   ├── advanced_metrics.py          #   HHI, DSO, churn, outliers (vetorizado)
│       │   ├── categorizer.py               #   Classificação por regex
│       │   ├── llm_insights.py              #   Diagnóstico executivo via LLM
│       │   ├── metrics_cache.py             #   Cache TTL thread-safe por job
│       │   ├── dataset_stats.py             #   Snapshot global para prompt RAG
│       │   ├── embedding_client.py          #   Singleton OpenAI Embeddings
│       │   ├── rag_indexer.py               #   Indexação vetorial em lotes paralelos
│       │   ├── sql_tools.py                 #   Queries parametrizadas para o agente
│       │   ├── chat_history.py              #   Persistência de histórico por sessão
│       │   ├── prompt_safety.py             #   Anti prompt-injection
│       │   ├── answer_validator.py          #   Anti alucinação (grounding de IDs)
│       │   ├── observability.py             #   Langfuse opt-in (no-op se desabilitado)
│       │   │
│       │   └── agent/                       #   🤖 Agente RAG conversacional
│       │       ├── __init__.py              #     Re-exports públicos
│       │       ├── prompts.py               #     System prompt + tool schemas
│       │       ├── context.py               #     AgentContext (fontes acumuladas)
│       │       ├── tools.py                 #     Dispatch das 6 ferramentas
│       │       └── runner.py                #     Executores sync + streaming
│       │
│       └── workers/                         # ⚡ Pipelines assíncronos
│           └── ingestion.py                 #   Orquestração ETL → LLM → RAG
│
│   └── tests/                               # 🧪 58 testes (pytest)
│       ├── conftest.py                      #   Stubs de psycopg para CI sem banco
│       ├── test_analytics.py
│       ├── test_answer_validator.py
│       ├── test_categorizer.py
│       ├── test_chat_stream.py
│       ├── test_etl.py
│       └── test_pipeline_integration.py
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    └── src/
        ├── app/
        │   ├── page.tsx                     # SPA principal (orquestra fases)
        │   ├── layout.tsx                   # Layout global + fontes
        │   ├── globals.css                  # Design system (Tailwind)
        │   └── api/[...path]/route.ts       # Proxy seguro (injeta X-API-Key)
        │
        ├── components/                      # 🎨 13 componentes React
        │   ├── UploadCard.tsx               #   Drag-and-drop de arquivo
        │   ├── ProgressTracker.tsx           #   Barra de progresso SSE
        │   ├── Dashboard.tsx                #   Grid de KPIs + gráficos
        │   ├── KpiCard.tsx                  #   Card individual de métrica
        │   ├── RevenueChart.tsx             #   Gráfico de receita temporal
        │   ├── CashflowBarChart.tsx          #   Barras de fluxo de caixa
        │   ├── InsightsPanel.tsx             #   Classificação + alertas IA
        │   ├── AdvancedInsightsPanel.tsx     #   Métricas avançadas (HHI, DSO)
        │   ├── ClientBehaviorChart.tsx       #   Perfil comportamental de clientes
        │   ├── TransactionsTable.tsx         #   Tabela paginada e filtrada
        │   ├── Chat.tsx                     #   Chat streaming com badges
        │   ├── ResumeJobCard.tsx             #   Recuperar job anterior
        │   └── ErrorBoundary.tsx             #   Fallback de erro por seção
        │
        └── lib/                             # 🔧 Utilitários
            ├── api.ts                       #   Funções de fetch tipadas
            ├── sse.ts                       #   Cliente Server-Sent Events
            ├── utils.ts                     #   Helpers compartilhados
            └── types.ts                     #   Tipagem espelhada do backend
```

## Screenshots do Fluxo

> *Os componentes abaixo descrevem a experiência do usuário final.*

### 1. Upload de Arquivo
Tela inicial com drag-and-drop. Aceita `.csv` e `.xlsx`. Validação de formato em tempo real.

### 2. Progresso do Processamento
Barra de progresso com 6 fases: `Leitura → Higienização → Cálculo → IA → Persistência → Indexação`. Polling a cada 1 segundo com estado visual.

### 3. Dashboard Executivo
Grid de KPIs + gráficos de receita e fluxo de caixa. Painel lateral com classificação de saúde financeira e alertas priorizados por severidade.

### 4. Chat Inteligente
Interface de chat com streaming em tempo real. O usuário vê:
- Tokens sendo digitados progressivamente
- Badges animados mostrando quais ferramentas foram acionadas (`count_transactions`, `semantic_search`, etc.)
- Indicador de grounding (IDs verificados vs não verificados)
- Histórico persistido por sessão

### 5. Tabela de Transações
Listagem paginada com filtros por status, categoria, cliente, valor e data. Ordenação clicável em todas as colunas.

---

## Endpoints da API

| Método | Endpoint | Descrição |
|---|---|---|
| `GET` | `/api/health` | Liveness — processo está de pé |
| `GET` | `/api/health/db` | Readiness — banco responde |
| `POST` | `/api/upload` | Upload de CSV/XLSX |
| `GET` | `/api/status/{id}` | Progresso em tempo real (SSE) |
| `GET` | `/api/dashboard/{id}` | KPIs + insights |
| `GET` | `/api/transactions/{id}` | Listagem paginada e filtrada |
| `GET` | `/api/insights/advanced/{id}` | Métricas avançadas (cacheadas) |
| `POST` | `/api/chat/stream` | Chat com streaming (SSE) |
| `GET` | `/api/chat/history/{id}/{session}` | Histórico da conversa |

---


## Licença

Autor: Lucas Abreu - https://github.com/lucasabreuzip/

Licença: [LICENSE](LICENSE)

<div align="center">

**Feito com foco em robustez, segurança e experiência do usuário. 💜**

[Voltar ao topo](#plataforma-de-inteligência-financeira-ia)

</div>
