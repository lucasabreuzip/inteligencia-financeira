"""
Singleton cacheado do cliente OpenAIEmbeddings.
"""
from __future__ import annotations

from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_embedding_client() -> OpenAIEmbeddings:
    settings = get_settings()
    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
        # OpenAI SDK faz backoff exponencial nativo; 5 retries cobre a maioria
        # dos 429/503 transitorios sem atrasar excessivamente jobs saudaveis.
        max_retries=5,
        # Chunk interno: quantos docs por chamada OpenAI. Fica bem abaixo do
        # limite de 2048/req e mantem latencia por chamada razoavel.
        chunk_size=500,
        # Timeout generoso: embeddings em batch podem levar 30-60s em picos.
        timeout=60.0,
    )
