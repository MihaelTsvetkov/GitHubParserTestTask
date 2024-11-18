from cloud_function.github_parser import fetch_activity_for_repo
from aioresponses import aioresponses
from datetime import datetime, timedelta, timezone
import pytest
import aiohttp

MOCK_ACTIVITY = [
    {"repo": "test_owner/test_repo", "date": "2024-11-01", "commits": 10, "authors": ["Author1", "Author2"]},
    {"repo": "test_owner/test_repo", "date": "2024-11-02", "commits": 5, "authors": ["Author1"]},
]


@pytest.mark.asyncio
async def test_fetch_activity_for_repo():
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=7)

    url = (
        f"https://api.github.com/repos/test_owner/test_repo/commits"
        f"?since={start_date.isoformat()}T00:00:00Z"
        f"&until={end_date.isoformat()}T23:59:59Z"
    )

    with aioresponses() as mocked:
        mocked.get(
            url,
            status=200,
            payload=[
                {
                    "commit": {
                        "author": {
                            "date": f"{start_date}T10:00:00Z",
                            "name": "Author1",
                        }
                    }
                },
                {
                    "commit": {
                        "author": {
                            "date": f"{end_date}T11:00:00Z",
                            "name": "Author2",
                        }
                    }
                },
            ],
        )

        async with aiohttp.ClientSession() as session:
            activity = await fetch_activity_for_repo(session, "test_owner/test_repo", 7)

        assert len(activity) == 2
        assert activity[0]["date"] == str(start_date)
        assert "Author1" in activity[0]["authors"]
