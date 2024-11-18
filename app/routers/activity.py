from datetime import datetime
from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from app.database.db import get_db_pool, fetch_activity_from_db, parse_date
from app.schemas.activity_schema import ActivitySchema, MessageResponseSchema
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{owner}/{repo}/activity", response_model=List[Union[ActivitySchema, MessageResponseSchema]])
async def get_activity(
    owner: str,
    repo: str,
    start_date: str,
    end_date: str,
    db_pool=Depends(get_db_pool)
):
    """
    Получение активности репозитория за указанный период.

    :param owner: Владелец репозитория.
    :param repo: Название репозитория.
    :param start_date: Начальная дата интервала (в формате YYYY-MM-DD).
    :param end_date: Конечная дата интервала (в формате YYYY-MM-DD).
    :param db_pool: Пул соединений с базой данных (зависимость FastAPI).
    :return: Список активности или сообщение, если данных нет.
    :raises HTTPException: При ошибке обработки запроса или внутренней ошибке сервера.
    """
    try:
        start_date_parsed = parse_date(start_date)
        end_date_parsed = parse_date(end_date)

        activity = await fetch_activity_from_db(
            pool=db_pool,
            repo=f"{owner}/{repo}",
            start_date=start_date_parsed,
            end_date=end_date_parsed,
        )

        if not activity:
            logger.info(f"Данные отсутствуют для репозитория {owner}/{repo} за указанный период.")
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Указанный интервал слишком большой, данных нет в базе.",
                    "activity": []
                }
            )

        min_date = activity[0]["date"]

        logger.info(
            f"min_date: {min_date} ({type(min_date)}), start_date_parsed: {start_date_parsed} ({type(start_date_parsed)})"
        )

        if isinstance(min_date, str):
            min_date = datetime.strptime(min_date, "%Y-%m-%d").date()

        logger.info(f"Activity: {activity}")

        if min_date > start_date_parsed:
            logger.warning(
                f"Запрашиваемый интервал с {start_date_parsed} превышает минимально доступную дату {min_date}."
            )
            return [
                {"message": f"Указанный интервал слишком большой, данные доступны только с {min_date}."},
                *activity,
            ]

        return activity

    except ValueError as e:
        logger.error(f"Некорректный формат даты: {e}")
        raise HTTPException(
            status_code=400,
            detail="Ошибка при обработке вашего запроса. Проверьте формат дат."
        )

    except Exception as e:
        logger.error(f"Ошибка при получении данных: {e}")
        raise HTTPException(
            status_code=500,
            detail="Произошла внутренняя ошибка сервера. Пожалуйста, повторите попытку позже.",
        )
