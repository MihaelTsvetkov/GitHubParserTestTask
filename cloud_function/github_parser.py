import asyncio
import aiohttp
import logging
import asyncpg
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("POSTGRES_HOST")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_NAME = os.getenv("POSTGRES_DB")
DB_PORT = os.getenv("POSTGRES_PORT")
ACTIVITY_DAYS = int(os.getenv("ACTIVITY_DAYS", 30))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"


async def get_top_repositories() -> List[Dict[str, Any]]:
    """
    Получает топ-100 репозиториев с GitHub.

    :return: Список репозиториев.
    """
    url = "https://api.github.com/search/repositories"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    params = {
        "q": "stars:>1",
        "sort": "stars",
        "order": "desc",
        "per_page": 100,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            response.raise_for_status()
            data = await response.json()

            if "items" not in data:
                raise ValueError("Ответ GitHub API не содержит ключа 'items'.")

            logger.info("Получены репозитории с GitHub")
            return data["items"]


async def fetch_activity_for_repo(
    session: aiohttp.ClientSession, repo_full_name: str, interval_days: int
) -> List[Dict[str, Any]]:
    """
    Получает информацию об активности репозитория через API GitHub.

    :param session: Сессия AIOHTTP.
    :param repo_full_name: Полное имя репозитория (owner/repo).
    :param interval_days: Количество дней для получения активности.
    :return: Список записей активности.
    """
    url = f"https://api.github.com/repos/{repo_full_name}/commits"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=interval_days)

    params = {
        "since": start_date.isoformat() + "T00:00:00Z",
        "until": end_date.isoformat() + "T23:59:59Z",
    }

    retries = 3
    logger.info(
        f"Начало обработки репозитория {repo_full_name}: "
        f"интервал с {start_date.isoformat()} по {end_date.isoformat()}."
    )

    while retries > 0:
        try:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                logger.info(f"Выполняется запрос к API для {repo_full_name}. URL: {response.url}")
                response.raise_for_status()
                commits = await response.json()

                if not commits:
                    logger.warning(
                        f"Репозиторий {repo_full_name} не содержит коммитов за последние {interval_days} дней."
                    )
                    return []

                logger.info(f"Получено {len(commits)} коммитов для репозитория {repo_full_name}.")

                activity = {}
                for commit in commits:
                    try:
                        commit_date = datetime.strptime(
                            commit["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ"
                        ).date()

                        if not (start_date <= commit_date <= end_date):
                            logger.warning(
                                f"Пропуск коммита с датой {commit_date} для {repo_full_name}, "
                                f"так как он не входит в заданный интервал."
                            )
                            continue

                        date_str = commit_date.strftime("%Y-%m-%d")
                        author = commit["commit"]["author"]["name"]
                        if date_str not in activity:
                            activity[date_str] = {"commits": 0, "authors": set()}
                        activity[date_str]["commits"] += 1
                        activity[date_str]["authors"].add(author)
                    except KeyError as e:
                        logger.error(f"Ошибка в данных коммита: {commit}. Отсутствует ключ: {e}")
                        continue

                return [
                    {"date": date, "commits": data["commits"], "authors": list(data["authors"])}
                    for date, data in activity.items()
                ]
        except aiohttp.ClientError as e:
            retries -= 1
            logger.warning(f"Ошибка соединения для {repo_full_name}: {e}. Осталось попыток: {retries}.")
            await asyncio.sleep(5)
        except asyncio.TimeoutError:
            retries -= 1
            logger.warning(f"Тайм-аут для {repo_full_name}. Осталось попыток: {retries}.")
            await asyncio.sleep(5)
        except Exception as e:
            logger.error(f"Неожиданная ошибка для {repo_full_name}: {e}")
            return []

    logger.error(f"Репозиторий {repo_full_name} не удалось обработать после нескольких попыток.")
    return []


async def save_activity_to_db(conn_or_pool, all_activities: List[Dict[str, Any]]) -> None:
    """
    Сохраняет активности в базу данных, удаляя старые записи перед вставкой новых.

    :param conn_or_pool: Либо соединение (asyncpg.Connection), либо пул (asyncpg.Pool).
    :param all_activities: Список активностей для сохранения.
    """
    if not all_activities:
        logger.warning("Нет данных для сохранения. Старые записи в базе данных не будут удалены.")
        return

    try:
        delete_query = "DELETE FROM activity;"
        insert_query = """
            INSERT INTO activity (repo, date, commits, authors)
            VALUES ($1, $2, $3, $4);
        """

        flattened_data = [
            (
                activity["repo"],
                datetime.strptime(activity["date"], "%Y-%m-%d").date(),
                activity["commits"],
                activity["authors"],
            )
            for activity in all_activities
        ]

        logger.info(f"Данные для сохранения: {flattened_data}")

        if isinstance(conn_or_pool, asyncpg.pool.Pool):
            async with conn_or_pool.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(delete_query)
                    await conn.executemany(insert_query, flattened_data)
        else:
            async with conn_or_pool.transaction():
                await conn_or_pool.execute(delete_query)
                await conn_or_pool.executemany(insert_query, flattened_data)

        logger.info("Активности успешно сохранены в базу данных.")
    except Exception as e:
        logger.error(f"Ошибка сохранения активностей: {e}")
        raise


async def save_repositories_to_db(conn, repositories: List[Dict[str, Any]]) -> None:
    """
    Сохраняет данные о репозиториях в таблицу top100, удаляя старые записи и обновляя поле prev из current.

    :param conn: Соединение AsyncPG.
    :param repositories: Список репозиториев.
    """
    try:
        repo_data = [
            {
                "repo": repo["full_name"],
                "owner": repo["owner"]["login"],
                "stars": repo.get("stargazers_count", 0),
                "watchers": repo.get("watchers_count", 0),
                "forks": repo.get("forks_count", 0),
                "open_issues": repo.get("open_issues_count", 0),
                "language": repo.get("language", "Unknown"),
                "position_cur": position,
            }
            for position, repo in enumerate(repositories, start=1)
        ]

        repo_names = [repo["repo"] for repo in repo_data]
        query_delete_old = """
            DELETE FROM top100
            WHERE repo NOT IN (SELECT UNNEST($1::text[]))
        """
        await conn.execute(query_delete_old, repo_names)

        logger.info("Старые записи успешно удалены.")

        query_fetch_existing = """
            SELECT repo, position_cur
            FROM top100
        """
        existing_records = await conn.fetch(query_fetch_existing)
        existing_map = {record["repo"]: record["position_cur"] for record in existing_records}

        query_insert_or_update = """
            INSERT INTO top100 (repo, owner, position_cur, position_prev, stars, watchers, forks, open_issues, language)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (repo) DO UPDATE
            SET position_cur = EXCLUDED.position_cur,
                position_prev = EXCLUDED.position_prev,
                owner = EXCLUDED.owner,
                stars = EXCLUDED.stars,
                watchers = EXCLUDED.watchers,
                forks = EXCLUDED.forks,
                open_issues = EXCLUDED.open_issues,
                language = EXCLUDED.language;
        """
        insert_data = [
            (
                repo["repo"],
                repo["owner"],
                repo["position_cur"],
                existing_map.get(repo["repo"]),
                repo["stars"],
                repo["watchers"],
                repo["forks"],
                repo["open_issues"],
                repo["language"],
            )
            for repo in repo_data
        ]

        await conn.executemany(query_insert_or_update, insert_data)

        logger.info("Данные о репозиториях успешно сохранены.")
    except Exception as e:
        logger.error(f"Ошибка сохранения репозиториев: {e}")
        raise


async def run_parser():
    """
    Основная логика парсера для получения и сохранения данных о репозиториях и их активности.
    """
    pool = await asyncpg.create_pool(DB_URL)

    try:
        repositories = await get_top_repositories()

        if not repositories:
            logger.warning("Не удалось получить ни одного репозитория.")
            return

        async with pool.acquire() as conn:
            async with conn.transaction():
                await save_repositories_to_db(conn, repositories)

                async with aiohttp.ClientSession() as session:
                    tasks = [
                        fetch_activity_for_repo(session, repo["full_name"], ACTIVITY_DAYS)
                        for repo in repositories
                    ]

                    activities = await asyncio.gather(*tasks, return_exceptions=True)

                    all_activities = []
                    for repo, activity in zip(repositories, activities):
                        if isinstance(activity, Exception):
                            logger.error(f"Ошибка при обработке {repo['full_name']}: {activity}")
                            continue
                        for record in activity:
                            record["repo"] = repo["full_name"]
                            all_activities.append(record)

                    await save_activity_to_db(conn, all_activities)

        logger.info("Все операции успешно выполнены.")
    except Exception as e:
        logger.error(f"Ошибка во время выполнения парсера: {e}")
    finally:
        await pool.close()
        logger.info("Парсер завершил работу.")


def handler(event, context):
    """
    Обработчик для запуска парсера через Яндекс облако.

    :param event: Событие.
    :param context: Контекст выполнения.
    """
    asyncio.run(run_parser())
    logger.info("Парсер успешно запущен!")
    return {"statusCode": 200, "body": "Парсер успешно выполнен"}
