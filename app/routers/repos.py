from fastapi import APIRouter, HTTPException, Depends, Query
from app.database.db import get_db_pool, fetch_top_repositories
from app.schemas.repo_schema import RepoSchema
from typing import Optional, List
from asyncpg.pool import Pool
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/top100", response_model=List[RepoSchema])
async def get_top_repositories(
    db_pool: Pool = Depends(get_db_pool),
    sort_by: Optional[str] = Query(
        "stars", description="Поле для сортировки (stars, watchers, forks, open_issues, language)"
    ),
    order: Optional[str] = Query("desc", description="Порядок сортировки (asc или desc)"),
):
    """
    Получение топ-100 репозиториев из базы данных.

    :param db_pool: Пул соединений с базой данных.
    :param sort_by: Поле для сортировки.
    :param order: Порядок сортировки (asc или desc).
    :return: Список репозиториев.
    """
    try:
        valid_sort_fields = ["stars", "watchers", "forks", "open_issues", "language"]
        valid_order_values = ["asc", "desc"]

        if sort_by not in valid_sort_fields:
            logger.error(f"Недопустимое поле для сортировки: {sort_by}")
            raise HTTPException(
                status_code=400,
                detail="Некорректное поле сортировки.",
            )

        if order not in valid_order_values:
            logger.error(f"Недопустимый порядок сортировки: {order}")
            raise HTTPException(
                status_code=400,
                detail="Некорректный порядок сортировки.",
            )

        repos = await fetch_top_repositories(db_pool, sort_by=sort_by, order=order)
        return [RepoSchema(**repo) for repo in repos]

    except HTTPException as http_err:
        logger.error(f"HTTPException: {http_err.detail}")
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении данных о репозиториях: {e}")
        raise HTTPException(
            status_code=500,
            detail="Произошла внутренняя ошибка сервера. Попробуйте позже."
        )
