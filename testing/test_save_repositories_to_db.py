from unittest.mock import AsyncMock

import pytest
from cloud_function.github_parser import save_repositories_to_db

MOCK_EXISTING_RECORDS = [
    {"repo": "test_owner/test_repo", "position_cur": 1},
    {"repo": "another_owner/another_repo", "position_cur": 2},
]

MOCK_REPOSITORIES = [
    {
        "full_name": "test_owner/test_repo",
        "owner": {"login": "test_owner"},
        "stargazers_count": 100,
        "watchers_count": 150,
        "forks_count": 20,
        "open_issues_count": 5,
        "language": "Python",
    },
    {
        "full_name": "another_owner/another_repo",
        "owner": {"login": "another_owner"},
        "stargazers_count": 200,
        "watchers_count": 300,
        "forks_count": 50,
        "open_issues_count": 10,
        "language": "JavaScript",
    },
]


@pytest.mark.asyncio
async def test_save_repositories_to_db(mocker):
    mock_conn = AsyncMock()

    mock_conn.fetch.return_value = MOCK_EXISTING_RECORDS

    await save_repositories_to_db(mock_conn, MOCK_REPOSITORIES)

    mock_conn.execute.assert_any_call(
        """
            DELETE FROM top100
            WHERE repo NOT IN (SELECT UNNEST($1::text[]))
        """,
        ["test_owner/test_repo", "another_owner/another_repo"],
    )

    expected_data = [
        (
            "test_owner/test_repo",
            "test_owner",
            1,
            1,
            100,
            150,
            20,
            5,
            "Python",
        ),
        (
            "another_owner/another_repo",
            "another_owner",
            2,
            2,
            200,
            300,
            50,
            10,
            "JavaScript",
        ),
    ]

    mock_conn.executemany.assert_called_once_with(
        """
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
        """,
        expected_data,
    )
