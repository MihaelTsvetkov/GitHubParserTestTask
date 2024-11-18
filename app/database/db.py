from typing import List, Dict, Any
from asyncpg import create_pool, Pool
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


DB_HOST = os.getenv("POSTGRES_HOST")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_PORT = os.getenv("POSTGRES_PORT")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def parse_date(date_str: str) -> datetime.date:
    """
    Преобразует строку даты в объект datetime.date.

    :param date_str: Дата в формате строки (YYYY-MM-DD).
    :return: Объект datetime.date.
    :raises ValueError: Если формат даты некорректен.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Неверный формат даты: {date_str}. Используйте YYYY-MM-DD.") from e


async def get_db_pool() -> Pool:
    """
    Создает пул соединений с базой данных.

    :return: Асинхронный пул соединений (Pool).
    """
    return await create_pool(DATABASE_URL)


async def fetch_activity_from_db(
    pool: Pool, repo: str, start_date: str, end_date: str
) -> List[Dict[str, Any]]:
    """
    Получение активности репозитория из таблицы activity.

    :param pool: Пул соединений с базой данных.
    :param repo: Полное имя репозитория (owner/repo).
    :param start_date: Начальная дата в формате YYYY-MM-DD.
    :param end_date: Конечная дата в формате YYYY-MM-DD.
    :return: Список объектов активности.
    """
    query = """
        SELECT date, commits, authors
        FROM activity
        WHERE repo = $1 AND date >= $2 AND date <= $3
        ORDER BY date ASC
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, repo, start_date, end_date)
    return [
        {"date": row["date"], "commits": row["commits"], "authors": row["authors"]}
        for row in rows
    ]


async def fetch_top_repositories(
    pool: Pool, sort_by: str = "stars", order: str = "desc", limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Получение топ-репозиториев из таблицы top100.

    :param pool: Пул соединений с базой данных.
    :param sort_by: Поле для сортировки (по умолчанию stars).
    :param order: Порядок сортировки (asc или desc).
    :param limit: Максимальное количество записей.
    :return: Список топ-репозиториев.
    """
    query = f"""
        SELECT repo, owner, position_cur, position_prev, stars, watchers, forks, open_issues, language
        FROM top100
        ORDER BY {sort_by} {order}
        LIMIT $1
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, limit)
    return [
        {
            "repo": row["repo"],
            "owner": row["owner"],
            "position_cur": row["position_cur"],
            "position_prev": row["position_prev"],
            "stars": row["stars"],
            "watchers": row["watchers"],
            "forks": row["forks"],
            "open_issues": row["open_issues"],
            "language": row["language"],
        }
        for row in rows
    ]
