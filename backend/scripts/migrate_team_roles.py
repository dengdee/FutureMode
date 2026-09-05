"""Preview role counts, or use --apply to convert retired owner roles atomically.

Run from backend: python -m scripts.migrate_team_roles [--apply]
This does not change the Alembic version; migration 0019 remains safe to reapply.
"""

import argparse
import asyncio

from sqlalchemy import text

from app.config import get_settings
from app.db.session import get_engine


async def run(apply: bool) -> None:
    settings = get_settings()
    engine = get_engine(settings.database_url, settings.db_pool_size, settings.db_max_overflow)
    try:
        async with engine.begin() as connection:
            for table in ("team_members", "team_invitations"):
                if apply:
                    result = await connection.execute(
                        text(f"UPDATE {table} SET role = 'admin' WHERE role = 'owner'")
                    )
                    print(f"{table}: converted={result.rowcount}")
                result = await connection.execute(
                    text(f"SELECT role, count(*) FROM {table} GROUP BY role ORDER BY role")
                )
                print(f"{table}: {result.all()}")
        print("Committed." if apply else "Preview only; no changes.")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    asyncio.run(run(parser.parse_args().apply))
