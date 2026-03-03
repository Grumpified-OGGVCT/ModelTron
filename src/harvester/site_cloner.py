"""src/harvester/site_cloner.py

Crawls an entire website and produces a navigable Markdown mirror:

    data/site_mirror/<domain>/
        _index.md          ← generated sitemap / navigation tree
        index.md           ← home page
        path/to/page.md    ← mirrors the URL path structure

All internal links are rewritten to relative .md paths so the mirror is
fully navigable in any Markdown renderer (GitHub, Obsidian, VS Code, etc.).
"""

import os
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md


class SiteCloner:
    def __init__(self, output_dir: str, max_pages: int = 500, delay: float = 1.0):
        """
        output_dir : root directory; mirror written to <output_dir>/<domain>/
        max_pages  : crawl cap (safety valve)
        delay      : seconds to sleep between HTTP requests
        """
        self.output_dir = output_dir
        self.max_pages = max_pages
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/115.0.0.0 Safari/537.36'
            )
        })

        # State populated during clone()
        self._base_domain: str = ""
        self._mirror_root: str = ""
        self._visited: set = set()
        self._url_to_path: dict = {}   # url → absolute local .md path
        self._page_titles: dict = {}   # url → page <title> text

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def clone(self, seed_url: str) -> str:
        """
        Crawl from seed_url, convert every discovered internal page to
        Markdown with rewritten internal links, and write a navigation index.
        Returns the mirror root directory path.
        """
        parsed = urlparse(seed_url)
        self._base_domain = parsed.netloc
        self._mirror_root = os.path.join(self.output_dir, self._base_domain)
        os.makedirs(self._mirror_root, exist_ok=True)

        print(f"[SiteCloner] Starting clone of {seed_url}")
        print(f"[SiteCloner] Output  : {self._mirror_root}")
        print(f"[SiteCloner] Max pages: {self.max_pages}")

        # ── Phase 1: Crawl ────────────────────────────────────────────
        queue = deque([self._normalize_url(seed_url, seed_url)])
        soups: dict = {}

        while queue and len(self._visited) < self.max_pages:
            url = queue.popleft()
            if url in self._visited:
                continue
            self._visited.add(url)

            soup = self._fetch(url)
            if soup is None:
                continue

            local_path = self._url_to_local(url)
            self._url_to_path[url] = local_path
            self._page_titles[url] = (
                soup.title.get_text(strip=True) if soup.title else url
            )
            soups[url] = soup

            for tag in soup.find_all('a', href=True):
                candidate = self._resolve(tag['href'], url)
                if candidate and candidate not in self._visited:
                    queue.append(candidate)

            time.sleep(self.delay)

        # ── Phase 2: Convert & save ───────────────────────────────────
        for url, soup in soups.items():
            self._save(url, soup)

        # ── Phase 3: Navigation index ─────────────────────────────────
        self._build_index(seed_url, len(soups))

        print(f"[SiteCloner] Done — {len(soups)} pages written to {self._mirror_root}")
        return self._mirror_root

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch(self, url: str):
        """GET url and return a BeautifulSoup, or None on failure."""
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, 'html.parser')
            print(f"[SiteCloner] HTTP {resp.status_code} — {url}")
        except Exception as exc:
            print(f"[SiteCloner] Error fetching {url}: {exc}")
        return None

    def _normalize_url(self, url: str, base: str) -> str:
        """Resolve a potentially relative URL, strip fragment and trailing slash."""
        abs_url = urljoin(base, url)
        abs_url, _ = urldefrag(abs_url)
        return abs_url.rstrip('/')

    def _resolve(self, href: str, base: str):
        """
        Return a normalised absolute URL if the href is an internal link,
        otherwise return None.
        """
        try:
            abs_url = self._normalize_url(href, base)
            p = urlparse(abs_url)
            if p.netloc != self._base_domain:
                return None
            if p.scheme not in ('http', 'https'):
                return None
            return abs_url
        except Exception:
            return None

    def _url_to_local(self, url: str) -> str:
        """Map a URL to an absolute local .md file path under the mirror root."""
        path = urlparse(url).path.rstrip('/')
        if not path:
            path = '/index'
        parts = [p for p in path.split('/') if p]
        return os.path.join(self._mirror_root, *parts) + '.md'

    def _rewrite_links(self, soup: BeautifulSoup, current_url: str) -> None:
        """Rewrite internal <a href> attributes to relative .md paths in-place."""
        current_path = self._url_to_path.get(current_url, '')
        current_dir = os.path.dirname(current_path) or self._mirror_root

        for tag in soup.find_all('a', href=True):
            candidate = self._resolve(tag['href'], current_url)
            if candidate and candidate in self._url_to_path:
                target = self._url_to_path[candidate]
                rel = os.path.relpath(target, current_dir)
                tag['href'] = rel.replace(os.sep, '/')  # forward slashes always

    def _save(self, url: str, soup: BeautifulSoup) -> None:
        """Convert a page to Markdown (with rewritten links) and write it to disk."""
        # Work on a copy so we don't mutate shared soup objects
        soup_copy = BeautifulSoup(str(soup), 'html.parser')
        self._rewrite_links(soup_copy, url)

        # Extract main content; try common content-area selectors first
        main = (
            soup_copy.find('div', id='content')
            or soup_copy.find('main')
            or soup_copy.find('article')
            or soup_copy.find('div', class_='pageContent')
            or soup_copy.body
        )
        html_content = str(main) if main else str(soup_copy)

        try:
            markdown = md(
                html_content,
                heading_style='ATX',
                bullets='-',
                strip=['script', 'style', 'nav', 'footer', 'iframe'],
            )
        except Exception as exc:
            print(f"[SiteCloner] markdownify error for {url}: {exc}")
            markdown = html_content  # fall back to raw HTML

        title = self._page_titles.get(url, url)
        header = (
            f"<!-- source: {url} -->\n"
            f"<!-- captured: {datetime.now(timezone.utc).date()} -->\n\n"
            f"# {title}\n\n"
        )
        content = header + markdown.strip() + '\n'

        local_path = self._url_to_path[url]
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'w', encoding='utf-8') as fh:
            fh.write(content)

    def _build_index(self, seed_url: str, total: int) -> None:
        """Write _index.md — a fully-linked, alphabetically-sorted navigation tree."""
        tree: dict = defaultdict(list)
        for url, path in self._url_to_path.items():
            rel = os.path.relpath(path, self._mirror_root)
            parts = rel.split(os.sep)
            folder = '/'.join(parts[:-1]) if len(parts) > 1 else ''
            tree[folder].append((url, path))

        lines = [
            f"# {self._base_domain} — Site Mirror\n",
            f"**Source:** {seed_url}  ",
            f"**Captured:** {datetime.now(timezone.utc).date()}  ",
            f"**Pages cloned:** {total}\n",
            "---\n",
            "## Navigation\n",
        ]

        for folder in sorted(tree.keys()):
            if folder:
                lines.append(f"\n### `{folder}/`\n")
            for url, path in sorted(tree[folder], key=lambda x: x[1]):
                rel = os.path.relpath(path, self._mirror_root).replace(os.sep, '/')
                title = self._page_titles.get(url, rel)
                lines.append(f"- [{title}]({rel})")

        index_path = os.path.join(self._mirror_root, '_index.md')
        with open(index_path, 'w', encoding='utf-8') as fh:
            fh.write('\n'.join(lines) + '\n')
        print(f"[SiteCloner] Navigation index → {index_path}")
