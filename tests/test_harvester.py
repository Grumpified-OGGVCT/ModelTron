import sqlite3
from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup

from src.harvester.engine import Harvester


@pytest.fixture
def db_file(tmp_path):
    return str(tmp_path / "vault.db")


def test_init_db_creates_tables(db_file):
    Harvester(db_file)
    conn = sqlite3.connect(db_file)
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    assert "threads" in tables
    assert "posts" in tables


def test_parse_and_store_records_thread(db_file):
    h = Harvester(db_file)
    soup = BeautifulSoup(
        "<html><head><title>Test Thread</title></head><body></body></html>",
        "html.parser",
    )
    h._parse_and_store(soup, "https://example.com/thread/1", "live")

    conn = sqlite3.connect(db_file)
    rows = conn.execute("SELECT url, title FROM threads").fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "https://example.com/thread/1"
    assert rows[0][1] == "Test Thread"


def test_parse_and_store_deduplication(db_file):
    """Inserting the same post twice must not create a duplicate row."""
    h = Harvester(db_file)
    html = (
        '<html><head><title>T</title></head><body>'
        '<article class="message" id="p1" data-author="Alice">'
        '<div class="message-content">Hello world</div>'
        '</article></body></html>'
    )
    soup = BeautifulSoup(html, "html.parser")
    h._parse_and_store(soup, "https://example.com/thread/1", "live")
    h._parse_and_store(soup, "https://example.com/thread/1", "live")

    conn = sqlite3.connect(db_file)
    count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    assert count == 1


def test_parse_and_store_new_version_stored(db_file):
    """A post with different content (different hash) IS stored as a new row."""
    h = Harvester(db_file)
    make_html = lambda body: BeautifulSoup(
        f'<html><head><title>T</title></head><body>'
        f'<article class="message" id="p1" data-author="Alice">'
        f'<div class="message-content">{body}</div>'
        f'</article></body></html>',
        "html.parser",
    )
    h._parse_and_store(make_html("Version 1"), "https://example.com/t/1", "live")
    h._parse_and_store(make_html("Version 2"), "https://example.com/t/1", "wayback_oldest")

    conn = sqlite3.connect(db_file)
    count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
    assert count == 2


def test_fetch_html_returns_none_on_network_error(db_file):
    h = Harvester(db_file)
    with patch.object(h.session, "get", side_effect=Exception("timeout")):
        result = h._fetch_html("https://example.com")
    assert result is None


def test_fetch_html_returns_none_on_non_200(db_file):
    h = Harvester(db_file)
    mock_resp = type("R", (), {"status_code": 404})()
    with patch.object(h.session, "get", return_value=mock_resp):
        result = h._fetch_html("https://example.com")
    assert result is None


def test_get_wayback_urls_returns_empty_on_error(db_file):
    h = Harvester(db_file)
    with patch.object(h.session, "get", side_effect=Exception("network")):
        result = h._get_wayback_urls("https://example.com")
    assert result == []


def test_get_wayback_urls_parses_cdx(db_file):
    h = Harvester(db_file)
    cdx_json = [
        ["timestamp", "original"],
        ["20150101120000", "https://example.com/page"],
    ]
    mock_resp = type("R", (), {"json": lambda self: cdx_json, "status_code": 200})()
    with patch.object(h.session, "get", return_value=mock_resp):
        snapshots = h._get_wayback_urls("https://example.com/page")
    assert len(snapshots) == 1
    assert "20150101120000" in snapshots[0]["url"]
    assert snapshots[0]["timestamp"] == "2015-01-01T12:00:00+00:00"
