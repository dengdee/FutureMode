from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import Settings


def _async_database_url(database_url: str) -> str:
    parsed = urlsplit(database_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    sslmode = query.pop("sslmode", None)
    if sslmode and "ssl" not in query and sslmode != "disable":
        query["ssl"] = sslmode
    database_url = urlunsplit(parsed._replace(query=urlencode(query)))

    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


@lru_cache(maxsize=4)
def get_engine(database_url: str, pool_size: int, max_overflow: int) -> AsyncEngine:
    return create_async_engine(
        _async_database_url(database_url),
        pool_pre_ping=True,
        pool_size=pool_size,
        max_overflow=max_overflow,
    )


async def database_check(settings: Settings) -> str:
    if not settings.database_configured:
        return "not_configured"

    try:
        engine = get_engine(settings.database_url, settings.db_pool_size, settings.db_max_overflow)
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError, ValueError, TypeError, TimeoutError):
        return "unavailable"
    return "ok"
