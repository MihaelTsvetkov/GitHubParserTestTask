from fastapi import FastAPI, HTTPException
from app.routers import repos, activity
from app.database.db import get_db_pool
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="GitHub Repo Analytics API",
    description="API для анализа данных о популярных репозиториях GitHub",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def include_routers():
    """
    Подключает роутеры к приложению.
    """
    app.include_router(repos.router, prefix="/api/repos", tags=["Repositories"])
    app.include_router(activity.router, prefix="/api/repos", tags=["Activity"])


include_routers()

db_pool = None


@app.on_event("startup")
async def startup_event():
    """
    Обработчик события старта приложения.
    Инициализирует подключение к базе данных.
    """
    global db_pool
    try:
        db_pool = await get_db_pool()
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        logger.info("Успешное подключение к базе данных")
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных при старте: {e}")
        raise HTTPException(status_code=500, detail="Ошибка подключения к базе данных")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Обработчик события завершения приложения.
    Закрывает подключение к базе данных.
    """
    global db_pool
    if db_pool is not None:
        try:
            await db_pool.close()
            logger.info("Подключение к базе данных успешно закрыто")
        except Exception as e:
            logger.error(f"Ошибка при закрытии подключения к базе данных: {e}")
    logger.info("Приложение завершается")


@app.get("/")
async def root():
    """
    Корневой эндпоинт приложения.
    :return: Сообщение о работоспособности API.
    """
    return {"message": "GitHub Repo Analytics API работает!"}

