import asyncio
import sqlite3
import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# conftest.py has already mocked mcp/chromadb/sentence_transformers.
# We can now safely import server.py.
import src.mcp_server.server as srv

SCHEMA = Path(__file__).parent.parent / "src" / "vault" / "schema.sql"


def _make_test_db(tmp_path: str) -> str:
    db_path = os.path.join(tmp_path, "vault.db")
    conn = sqlite3.connect(db_path)
    with open(SCHEMA) as fh:
        conn.executescript(fh.read())
    conn.execute(
        "INSERT INTO threads (id, url, title) VALUES (1, 'https://example.com/t/1', 'Test Thread')"
    )
    conn.execute(
        """
        INSERT INTO posts
            (thread_id, post_external_id, author, content_clean,
             source_type, snapshot_date, content_hash)
        VALUES (1, 'p1', 'Alice', 'Ancient knowledge here', 'live', '2024-01-01', 'abc123')
        """
    )
    conn.commit()
    conn.close()
    return db_path


def test_view_thread_history_returns_post(tmp_path, monkeypatch):
    db_path = _make_test_db(str(tmp_path))
    monkeypatch.setattr(
        srv, 'get_db',
        lambda: sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    )

    result = asyncio.run(
        srv.call_tool("view_thread_history", {"url": "https://example.com/t/1"})
    )

    assert len(result) == 1
    assert "Alice" in result[0].text
    assert "Ancient knowledge here" in result[0].text
    assert "THREAD RECONSTRUCTION" in result[0].text


def test_view_thread_history_unknown_url_returns_empty_reconstruction(tmp_path, monkeypatch):
    db_path = _make_test_db(str(tmp_path))
    monkeypatch.setattr(
        srv, 'get_db',
        lambda: sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    )

    result = asyncio.run(
        srv.call_tool("view_thread_history", {"url": "https://nowhere.example.com"})
    )

    assert len(result) == 1
    assert "THREAD RECONSTRUCTION" in result[0].text
    # No post data — just the header line
    assert "Alice" not in result[0].text


def test_search_archives_returns_raw_header(monkeypatch):
    mock_embedder = MagicMock()
    mock_embedder.encode.return_value.tolist.return_value = [0.1] * 384
    monkeypatch.setattr(srv, 'embedder', mock_embedder)

    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        'documents': [["Ancient pyramid text"]],
        'metadatas': [[{'author': 'Bob', 'source': 'wayback_oldest'}]],
    }
    monkeypatch.setattr(srv, 'collection', mock_collection)

    result = asyncio.run(
        srv.call_tool("search_archives", {"query": "pyramids"})
    )

    assert len(result) == 1
    assert "--- RAW ARCHIVAL DATA ---" in result[0].text
    assert "Ancient pyramid text" in result[0].text
    assert "Bob" in result[0].text


def test_unknown_tool_returns_error_message():
    result = asyncio.run(srv.call_tool("nonexistent_tool", {}))
    assert len(result) == 1
    assert "Unknown tool" in result[0].text
