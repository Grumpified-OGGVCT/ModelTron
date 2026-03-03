CREATE TABLE IF NOT EXISTS threads (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    title TEXT,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER,
    post_external_id TEXT,
    author TEXT,
    content_raw TEXT,
    content_clean TEXT,
    source_type TEXT CHECK(source_type IN ('live', 'wayback_oldest', 'wayback_recent')),
    capture_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    snapshot_date DATETIME, -- The actual date of the snapshot
    content_hash TEXT,
    is_deleted BOOLEAN DEFAULT FALSE,
    UNIQUE(thread_id, post_external_id, content_hash),
    FOREIGN KEY(thread_id) REFERENCES threads(id)
);

CREATE INDEX idx_content_search ON posts(content_clean);
CREATE INDEX idx_posts_dedup_lookup ON posts(post_external_id, content_hash);
