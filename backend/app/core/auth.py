from fastapi import Header, HTTPException, status

from app.core.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Exige header `X-API-Key` válido.

    Protege endpoints internos sem montar OAuth completo — suficiente para
    este estágio, trocável por JWT/OAuth sem tocar nos routers.
    """
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida ou ausente.",
        )