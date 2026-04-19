# Inteligência Financeira

Plataforma para análise de dados financeiros a partir de CSVs de transações.

## Stack

- Backend: FastAPI (Python 3.12)
- Frontend: Next.js + TypeScript
- Banco: PostgreSQL

## Rodando

```bash
cp .env.example .env
docker compose up -d db
```

Banco em `localhost:5432` (user/senha/db: `finance`).