"""Apply only the safe invitation index change when the legacy migration chain is unavailable."""

import asyncio

from sqlalchemy import text

from app.config import get_settings
from app.db.session import get_engine


async def run():
    settings = get_settings()
    engine = get_engine(settings.database_url, settings.db_pool_size, settings.db_max_overflow)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_team_invite_pending "
                    "ON team_invitations (team_id, email) WHERE status = 'pending'"
                )
            )
            await connection.execute(
                text(
                    "ALTER TABLE team_invitations "
                    "DROP CONSTRAINT IF EXISTS uq_team_invite_email_status"
                )
            )
        print("Invitation index updated; all invitation records preserved.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run())
