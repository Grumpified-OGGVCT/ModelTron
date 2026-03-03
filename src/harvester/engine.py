import requests
import hashlib
import sqlite3
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import time


class Harvester:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        # Ensure SQLite enforces declared FOREIGN KEY constraints on this connection.
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_db(db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/115.0.0.0 Safari/537.36'
            )
        })

    def _init_db(self, db_path):
        """Apply schema.sql to initialise the database if needed."""
        import os
        schema_path = os.path.join(
            os.path.dirname(__file__), '..', 'vault', 'schema.sql'
        )
        schema_path = os.path.normpath(schema_path)
        with open(schema_path, 'r') as fh:
            self.conn.executescript(fh.read())
        self.conn.commit()

    def ingest_thread(self, url):
        print(f"[Harvester] Ingesting: {url}")

        # 1. Fetch Live Version — stamp with current UTC time
        live_soup = self._fetch_html(url)
        if live_soup:
            self._parse_and_store(
                live_soup, url, 'live',
                datetime.now(timezone.utc).isoformat(timespec='seconds')
            )

        # 2. Fetch Wayback (Temporal) Versions
        wayback_snapshots = self._get_wayback_urls(url)
        for snapshot in wayback_snapshots:
            wb_soup = self._fetch_html(snapshot['url'])
            if wb_soup:
                self._parse_and_store(
                    wb_soup, url, 'wayback_oldest', snapshot['timestamp']
                )
            time.sleep(2)  # Be nice to archives

    def _fetch_html(self, url):
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 200:
                return BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        return None

    def _get_wayback_urls(self, url):
        """Query CDX API for oldest snapshot."""
        cdx_url = (
            f"https://web.archive.org/cdx/search/cdx"
            f"?url={url}&output=json&fl=timestamp,original"
            f"&filter=statuscode:200"
        )
        try:
            resp = self.session.get(cdx_url, timeout=30)
            if resp.status_code != 200:
                return []
            data = resp.json()
            if len(data) <= 1:
                return []

            snapshots = []
            oldest = data[1]  # Index 0 is header
            # Parse CDX timestamp (YYYYMMDDHHmmss) into ISO-8601 UTC
            ts_iso = datetime.strptime(oldest[0], '%Y%m%d%H%M%S').replace(
                tzinfo=timezone.utc
            ).isoformat(timespec='seconds')
            snapshots.append({
                'timestamp': ts_iso,
                'url': f"https://web.archive.org/web/{oldest[0]}/{oldest[1]}"
            })
            return snapshots
        except Exception:
            return []

    def _parse_and_store(self, soup, url, source_type, snapshot_date=None):
        """XenForo parsing logic — stores posts into vault.db."""
        title = soup.title.string if soup.title else "Unknown"

        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO threads (url, title) VALUES (?, ?)",
            (url, title)
        )
        thread_id = cur.execute(
            "SELECT id FROM threads WHERE url = ?", (url,)
        ).fetchone()[0]

        posts = soup.find_all('article', class_='message')
        for post in posts:
            post_id = post.get('id')
            author = post.get('data-author', 'Unknown')
            content_div = post.find('div', class_='message-content')
            content_raw = str(content_div) if content_div else ""
            content_clean = (
                content_div.get_text(strip=True) if content_div else ""
            )

            # Integrity Hash
            content_hash = hashlib.sha256(
                f"{post_id}{content_clean}".encode()
            ).hexdigest()

            # Only store if this exact version does not already exist
            exists = cur.execute(
                "SELECT 1 FROM posts WHERE post_external_id = ? AND content_hash = ?",
                (post_id, content_hash)
            ).fetchone()
            if not exists:
                cur.execute(
                    """
                    INSERT INTO posts
                        (thread_id, post_external_id, author, content_raw,
                         content_clean, source_type, snapshot_date, content_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        thread_id, post_id, author, content_raw,
                        content_clean, source_type, snapshot_date, content_hash
                    )
                )

        self.conn.commit()
        print(f"[Harvester] Stored data from {source_type} for {url}")
