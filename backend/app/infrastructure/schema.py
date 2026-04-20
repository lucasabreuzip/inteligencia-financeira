"""
Schema DDL do banco de dados PostgreSQL + migrações idempotentes.
"""
from __future__ import annotations

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS jobs (
    job_id       TEXT PRIMARY KEY,
    filename     TEXT NOT NULL,
    status       TEXT NOT NULL,
    error        TEXT,
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id           TEXT NOT NULL,
    job_id       TEXT NOT NULL,
    valor        DOUBLE PRECISION NOT NULL,
    data         DATE NOT NULL,
    status       TEXT NOT NULL,
    cliente      TEXT NOT NULL,
    descricao    TEXT NOT NULL,
    categoria    TEXT NOT NULL DEFAULT 'outros',
    embedding    vector(1536),
    PRIMARY KEY (id, job_id),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_transactions_job ON transactions(job_id);
CREATE INDEX IF NOT EXISTS idx_transactions_data ON transactions(data);
CREATE INDEX IF NOT EXISTS idx_transactions_embedding ON transactions USING hnsw (embedding vector_cosine_ops);

-- Migracao idempotente: tabelas pre-existentes com data TEXT sao convertidas
-- para DATE. Permite upgrade in-place sem dropar o volume. Strings ISO
-- "YYYY-MM-DD" batem com ::DATE nativamente.
DO $migrate_data_type$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'transactions'
          AND column_name = 'data'
          AND data_type = 'text'
    ) THEN
        ALTER TABLE transactions ALTER COLUMN data TYPE DATE USING data::DATE;
    END IF;
END
$migrate_data_type$;

CREATE TABLE IF NOT EXISTS kpis (
    job_id               TEXT PRIMARY KEY,
    total_transacoes     INTEGER NOT NULL,
    receita_total        DOUBLE PRECISION NOT NULL,
    ticket_medio         DOUBLE PRECISION NOT NULL,
    taxa_inadimplencia   DOUBLE PRECISION NOT NULL,
    inadimplencia_valor  DOUBLE PRECISION NOT NULL,
    periodo_inicio       TEXT,
    periodo_fim          TEXT,
    ai_insights_json     TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS timeseries (
    job_id       TEXT NOT NULL,
    periodo      TEXT NOT NULL,
    receita      DOUBLE PRECISION NOT NULL,
    transacoes   INTEGER NOT NULL,
    PRIMARY KEY (job_id, periodo),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

-- Histórico de chat por sessão. session_id e gerado client-side (UUID em
-- localStorage) — permite multi-sessao por job no futuro sem migracao.
-- ON DELETE CASCADE: apagar o job limpa a conversa automaticamente.
CREATE TABLE IF NOT EXISTS chat_messages (
    id           BIGSERIAL PRIMARY KEY,
    job_id       TEXT NOT NULL,
    session_id   TEXT NOT NULL,
    role         TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content      TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session
    ON chat_messages(job_id, session_id, id);
"""
