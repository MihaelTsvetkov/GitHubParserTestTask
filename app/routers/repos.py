from asyncpg import PostgresError
from fastapi import APIRouter, HTTPException, Depends, Request
from app.database.db import fetch_top_repositories
from app.schemas.repo_schema import RepoSchema
from app.schemas.query_params import Top100QueryParams
from app.database.utils import get_db_pool
from typing import List
from asyncpg.pool import Pool
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/top100", response_model=List[RepoSchema])
async def get_top_repositories(
        request: Request,  
        params: Top100QueryParams = Depends(),  
        db_pool: Pool = Depends(get_db_pool),  
):
    """
    Получение топ-100 репозиториев из базы данных.

    :param request: Объект запроса для проверки всех параметров.
    :param params: Валидированные параметры запроса.
    :param db_pool: Пул соединений с базой данных.
    :return: Список репозиториев.
    """
    try:
        valid_params = {"sort_by", "order"}
        query_params = set(request.query_params.keys())
        unknown_params = query_params - valid_params

        if unknown_params:
            raise HTTPException(
                status_code=400,
                detail=f"Неизвестные параметры запроса: {', '.join(unknown_params)}"
            )

        logger.info(f"Получен запрос с параметрами: sort_by={params.sort_by}, order={params.order}")

        # Основная логика работы
        repos = await fetch_top_repositories(
            db_pool, sort_by=params.sort_by, order=params.order
        )

        if not repos:
            logger.warning("Данные не найдены в базе данных для запрошенных параметров.")
            raise HTTPException(
                status_code=404,
                detail="Репозитории не найдены."
            )

        return [RepoSchema(**repo) for repo in repos]

    except PostgresError as db_err:
        logger.error(f"Ошибка базы данных: {db_err}")
        raise HTTPException(
            status_code=500,
            detail="Ошибка соединения с базой данных. Попробуйте позже."
        )
    except HTTPException as http_err:
        logger.warning(f"Обработка HTTP-ошибки: {http_err.detail}")
        raise http_err
    except Exception as e:
        logger.error(f"Необработанная ошибка: {e}")
        raise HTTPException(
            status_code=500,
            detail="Произошла внутренняя ошибка сервера. Попробуйте позже."
        )
