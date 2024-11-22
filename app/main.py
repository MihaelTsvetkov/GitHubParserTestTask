from fastapi import FastAPI, HTTPException
from app.routers import repos, activity
from fastapi.middleware.cors import CORSMiddleware
from asyncpg import create_pool
from app.database.utils import set_db_pool
from app.config.config import Settings
import logging
from dotenv import load_dotenv

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


@app.on_event("startup")
async def startup_event():
    """
    Инициализация подключения к базе данных при старте приложения.
    """
    try:
        load_dotenv()
        settings = Settings()
        pool = await create_pool(dsn=settings.database_url)
        await set_db_pool(pool)
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        logger.info("Успешное подключение к базе данных")
    except Exception as e:
        logger.error(f"Ошибка подключения к базе данных: {e}")
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
