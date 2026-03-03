import os

import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch

from src.harvester.site_cloner import SiteCloner


@pytest.fixture
def cloner(tmp_path):
    c = SiteCloner(output_dir=str(tmp_path), max_pages=10, delay=0)
    c._base_domain = "example.com"
    c._mirror_root = str(tmp_path / "example.com")
    os.makedirs(c._mirror_root, exist_ok=True)
    return c


# ── URL → local path mapping ─────────────────────────────────────────────────

def test_url_to_local_root(cloner):
    path = cloner._url_to_local("https://example.com")
    assert path.endswith("index.md")


def test_url_to_local_root_with_slash(cloner):
    path = cloner._url_to_local("https://example.com/")
    assert path.endswith("index.md")


def test_url_to_local_single_segment(cloner):
    path = cloner._url_to_local("https://example.com/threads")
    assert path.endswith(os.path.join("threads.md"))


def test_url_to_local_nested(cloner):
    path = cloner._url_to_local("https://example.com/forums/general")
    assert path.endswith(os.path.join("forums", "general.md"))


def test_url_to_local_traversal(cloner):
    # Malicious path with traversal
    path = cloner._url_to_local("https://example.com/../../etc/passwd")
    # Should be sanitized to just etc/passwd.md under mirror root, or similar
    assert ".." not in path
    assert "etc/passwd" in path.replace(os.sep, "/")


def test_url_to_local_sanitization(cloner):
    # Path with special characters
    path = cloner._url_to_local("https://example.com/path;with?query=and#fragment")
    # urlparse strips query and fragment from .path
    # ';' is often part of the path in some old URL specs but urlparse might handle it differently
    assert "path.md" in path.replace(os.sep, "/")


# ── Link resolution ──────────────────────────────────────────────────────────

def test_resolve_relative_link(cloner):
    result = cloner._resolve("/threads/1", "https://example.com/index")
    assert result == "https://example.com/threads/1"


def test_resolve_absolute_internal_link(cloner):
    result = cloner._resolve("https://example.com/page", "https://example.com/")
    assert result == "https://example.com/page"


def test_resolve_external_link_returns_none(cloner):
    result = cloner._resolve("https://other.com/page", "https://example.com/")
    assert result is None


def test_resolve_strips_fragment(cloner):
    result = cloner._resolve("/page#section", "https://example.com/")
    assert result == "https://example.com/page"


# ── Navigation index ─────────────────────────────────────────────────────────

def test_build_index_creates_file(tmp_path):
    c = SiteCloner(str(tmp_path), delay=0)
    c._base_domain = "example.com"
    c._mirror_root = str(tmp_path / "example.com")
    os.makedirs(c._mirror_root, exist_ok=True)

    c._url_to_path = {
        "https://example.com":              str(tmp_path / "example.com" / "index.md"),
        "https://example.com/threads/foo":  str(tmp_path / "example.com" / "threads" / "foo.md"),
    }
    c._page_titles = {
        "https://example.com":             "Home",
        "https://example.com/threads/foo": "Foo Thread",
    }
    c._build_index("https://example.com", 2)

    index_path = tmp_path / "example.com" / "_index.md"
    assert index_path.exists()
    content = index_path.read_text()
    assert "# example.com" in content   # exact heading written by _build_index
    assert "Home" in content
    assert "Foo Thread" in content
    assert "index.md" in content
    assert "threads/foo.md" in content


# ── Full clone with mocked HTTP ──────────────────────────────────────────────

def test_clone_creates_markdown_files(tmp_path):
    home_html = (
        "<html><head><title>Home</title></head><body>"
        '<a href="/page1">Page 1</a>'
        '<a href="https://external.com/x">External</a>'
        "</body></html>"
    )
    page1_html = (
        "<html><head><title>Page 1</title></head><body>"
        '<a href="/">Back Home</a>'
        "<p>Content here</p>"
        "</body></html>"
    )

    def mock_fetch(url):
        if url == "https://example.com":
            return BeautifulSoup(home_html, "html.parser")
        if url == "https://example.com/page1":
            return BeautifulSoup(page1_html, "html.parser")
        return None

    c = SiteCloner(str(tmp_path), max_pages=5, delay=0)
    with patch.object(c, "_fetch", side_effect=mock_fetch):
        c.clone("https://example.com")

    mirror = tmp_path / "example.com"
    assert (mirror / "index.md").exists()
    assert (mirror / "page1.md").exists()
    assert (mirror / "_index.md").exists()


def test_clone_rewrites_internal_links(tmp_path):
    """Internal links must become relative .md paths in the output."""
    home_html = (
        "<html><head><title>Home</title></head><body>"
        '<a href="/page1">Page 1</a>'
        "</body></html>"
    )
    page1_html = (
        "<html><head><title>Page 1</title></head><body>"
        '<p>Content</p>'
        "</body></html>"
    )

    def mock_fetch(url):
        mapping = {
            "https://example.com": home_html,
            "https://example.com/page1": page1_html,
        }
        raw = mapping.get(url)
        return BeautifulSoup(raw, "html.parser") if raw else None

    c = SiteCloner(str(tmp_path), max_pages=5, delay=0)
    with patch.object(c, "_fetch", side_effect=mock_fetch):
        c.clone("https://example.com")

    home_content = (tmp_path / "example.com" / "index.md").read_text()
    # The link to /page1 should have been rewritten to page1.md
    assert "page1.md" in home_content


def test_clone_preserves_external_links(tmp_path):
    """External links must NOT be rewritten to .md paths."""
    home_html = (
        "<html><head><title>Home</title></head><body>"
        '<a href="https://external.com/x">External</a>'
        "</body></html>"
    )

    def mock_fetch(url):
        if url == "https://example.com":
            return BeautifulSoup(home_html, "html.parser")
        return None

    c = SiteCloner(str(tmp_path), max_pages=5, delay=0)
    with patch.object(c, "_fetch", side_effect=mock_fetch):
        c.clone("https://example.com")

    home_content = (tmp_path / "example.com" / "index.md").read_text()
    assert "https://external.com/x" in home_content
