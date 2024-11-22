from asyncpg.pool import Pool
from fastapi import HTTPException

db_pool: Pool = None


async def get_db_pool() -> Pool:
    """
    Возвращает пул соединений с базой данных.
    """
    global db_pool
    if db_pool is None:
        raise HTTPException(status_code=500, detail="База данных временно недоступна.")
    return db_pool


async def set_db_pool(pool: Pool):
    """
    Устанавливает глобальный пул соединений с базой данных.
    """
    global db_pool
    db_pool = pool
