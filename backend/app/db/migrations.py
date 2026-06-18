"""Minimal, idempotent schema patcher for additive column changes.

`Base.metadata.create_all()` (called in `init_db()`) only creates tables
that don't exist yet — it never ALTERs an existing table to add a new
column. This project doesn't run Alembic migrations, so without this
helper, every column added to an *already-deployed* table (like
`users.role` and `tours.schedule` below) would simply never reach
production: the app would crash on first query with
"column users.role does not exist".

This module is intentionally small and append-only: each time a new
column is added to an existing model, add one matching block here. For
a project this size that's a reasonable trade-off; if/when the schema
churn grows, introduce Alembic instead of growing this file forever.
"""

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncConnection


async def _existing_tables(conn: AsyncConnection) -> set[str]:
    return set(await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names()))


async def _existing_columns(conn: AsyncConnection, table: str) -> set[str]:
    cols = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_columns(table))
    return {c["name"] for c in cols}


async def run_lightweight_migrations(conn: AsyncConnection) -> None:
    tables = await _existing_tables(conn)

    if "users" in tables:
        cols = await _existing_columns(conn, "users")
        if "role" not in cols:
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN role VARCHAR(16) NOT NULL DEFAULT 'user'")
            )
            # Backfill: anyone already flagged admin under the legacy
            # boolean keeps full admin rights under the new role system.
            await conn.execute(text("UPDATE users SET role = 'admin' WHERE is_admin = true"))
        if "force_password_change" not in cols:
            await conn.execute(
                text(
                    "ALTER TABLE users ADD COLUMN force_password_change "
                    "BOOLEAN NOT NULL DEFAULT false"
                )
            )

    if "tours" in tables:
        cols = await _existing_columns(conn, "tours")
        if "schedule" not in cols:
            await conn.execute(
                text(
                    "ALTER TABLE tours ADD COLUMN schedule VARCHAR(32) "
                    "NOT NULL DEFAULT 'По запросу'"
                )
            )
