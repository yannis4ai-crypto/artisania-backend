from contextlib import asynccontextmanager

import asyncpg

from config import settings

_pool: asyncpg.Pool | None = None


async def init_pool() -> None:
    global _pool
    try:
        _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5)
    except (OSError, asyncpg.PostgresError):
        # Pas de Postgres local requis pour dev/tests unitaires — acquire()
        # bascule sur une connexion ad-hoc si le pool n'a jamais démarré.
        _pool = None


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def acquire():
    if _pool is not None:
        async with _pool.acquire() as conn:
            yield conn
        return
    conn = await asyncpg.connect(settings.database_url)
    try:
        yield conn
    finally:
        await conn.close()
