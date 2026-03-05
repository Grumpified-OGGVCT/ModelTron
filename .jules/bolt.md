YYYY-MM-DD - [FastAPI SQLite Connection Pooling Optimization]
Context: SQLite connections in FastAPI dependency (`get_db`) were being opened and closed on every request. This caused major blocking and performance bottleneck during high concurrent load.
Learning: In a heavily synchronous environment like FastAPI with standard `def` endpoints, re-opening a SQLite connection is an expensive disk I/O block.
Evidence: Sequential 5000 POST requests took ~46.3s, GET requests took ~61.8s. After optimizing to a single global connection with `check_same_thread=False` and WAL mode: POST took ~35.1s, GET took ~54.3s.
Action: Utilize a thread-safe global connection pool (`check_same_thread=False` with WAL mode enabled) for SQLite databases accessed via `Depends` when rewriting them to async is not an option. Keep cache size optimized (`PRAGMA cache_size=-64000;`).
