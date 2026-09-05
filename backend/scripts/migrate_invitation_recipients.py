"""Apply only migration 0021 while the legacy Alembic chain is incomplete."""
import asyncio
from importlib import import_module

from sqlalchemy import text

from app.config import get_settings
from app.db.session import get_engine


async def run():
    settings = get_settings()
    engine = get_engine(settings.database_url, settings.db_pool_size, settings.db_max_overflow)
    try:
        async with engine.begin() as connection:
            for statement in import_module(
                "migrations.versions.0021_invitation_recipients"
            ).STATEMENTS:
                await connection.execute(text(statement))
        print("Recipient columns and index ready; legacy invitations preserved unassigned.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run())
