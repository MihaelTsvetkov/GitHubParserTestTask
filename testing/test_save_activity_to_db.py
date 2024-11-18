from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
import pytest
from cloud_function.github_parser import save_activity_to_db


MOCK_ACTIVITY = [
    {"repo": "test_owner/test_repo", "date": "2024-11-01", "commits": 10, "authors": ["Author1", "Author2"]},
    {"repo": "test_owner/test_repo", "date": "2024-11-02", "commits": 5, "authors": ["Author1"]},
]


@pytest.mark.asyncio
async def test_save_activity_to_db():
    mock_conn = MagicMock()
    mock_transaction = AsyncMock()
    mock_conn.transaction.return_value = mock_transaction
    mock_conn.execute = AsyncMock()
    mock_conn.executemany = AsyncMock()

    await save_activity_to_db(mock_conn, MOCK_ACTIVITY)

    mock_conn.execute.assert_called_once_with("DELETE FROM activity;")

    actual_query = mock_conn.executemany.call_args[0][0].replace(" ", "").replace("\n", "")
    expected_query = """
        INSERT INTO activity (repo, date, commits, authors)
        VALUES ($1, $2, $3, $4);
    """.replace(" ", "").replace("\n", "")

    assert actual_query == expected_query, f"Actual query: {actual_query}, Expected query: {expected_query}"

    actual_data = mock_conn.executemany.call_args[0][1]
    expected_data = [
        ("test_owner/test_repo", datetime(2024, 11, 1).date(), 10, ["Author1", "Author2"]),
        ("test_owner/test_repo", datetime(2024, 11, 2).date(), 5, ["Author1"]),
    ]
    assert actual_data == expected_data, f"Actual data: {actual_data}, Expected data: {expected_data}"
