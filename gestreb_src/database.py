"""
Configuration de la connexion PostgreSQL avec asyncpg (async).
"""

import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

# Pool de connexions global
_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Retourne le pool de connexions (singleton)."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            port=int(os.getenv("DB_PORT", "5432")),
            password=os.getenv("DB_PWD"),
            database=os.getenv("DB_NAME"),
            ssl="require",
            min_size=2,
            max_size=10,
        )
    return _pool


async def close_pool():
    """Ferme le pool de connexions proprement."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_db():
    """
    Dépendance FastAPI : fournit une connexion depuis le pool.
    Utilisation : db: asyncpg.Connection = Depends(get_db)
    """
    pool = await get_pool()
    async with pool.acquire() as connection:
        yield connection
