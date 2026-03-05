CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    verified_specs JSON,
    unverified_claims JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evaluations (
    id TEXT PRIMARY KEY,
    model_id TEXT,
    category TEXT,
    score REAL,
    metrics JSON,
    verification_method TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(model_id) REFERENCES models(id)
);

CREATE TABLE IF NOT EXISTS cache (
    idempotency_key TEXT PRIMARY KEY,
    response JSON,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
