from aioresponses import aioresponses
import pytest
from cloud_function.github_parser import get_top_repositories


@pytest.mark.asyncio
async def test_get_top_repositories():
    url = "https://api.github.com/search/repositories?q=stars%3A%3E1&sort=stars&order=desc&per_page=100"
    with aioresponses() as mocked:
        mocked.get(
            url,
            payload={"items": [{"full_name": "test/repo1"}, {"full_name": "test/repo2"}]},
        )

        repos = await get_top_repositories()

        assert len(repos) == 2
        assert repos[0]["full_name"] == "test/repo1"
