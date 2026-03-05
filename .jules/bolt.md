# BOLT ⚡ — Performance Journal

2026-03-03 - Initial Baseline Established
Context: Starting optimization of ModelTron's API and SQLite interaction. Discovered heavy reliance on synchronous SQLite connections inside FastAPI dependency injection.
Learning: The current `get_db` generator yields a synchronous SQLite connection which is then used across FastAPI's async context managers/threadpools. Under concurrent load (50 workers, 500 requests), this immediately throws `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.` This causes a 100% error rate for all database-bound requests (`/v1/rankings`, `/v1/recommend`, `/v1/evaluate`). Only `/v1/health` and `/v1/benchmarks` succeed.
Evidence: 500 total requests at 50 concurrency. 209 requests completed before server crash/abort. Throughput: ~87 req/sec. Error rate on DB endpoints: 100%.
Action: The highest priority is to implement `aiosqlite` and an async dependency injection pattern to handle connection pooling safely across event loops. This will stabilize the application under load before we optimize individual endpoints.

2026-03-03 - Phase 2: Foundation & Architecture Completed
Context: Replaced synchronous `sqlite3` with `aiosqlite` and migrated DB schema initialization to FastAPI `lifespan` events.
Learning: By utilizing `aiosqlite`, we solve the cross-thread `sqlite3.ProgrammingError` encountered during concurrent execution. Adding `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL` improves concurrency handling under load.
Note: Migrating to `aiosqlite` means the endpoints themselves must be refactored to use `await` when interacting with the database. Tests are failing right now because the synchronous endpoints are trying to `.fetchone()` on an un-awaited aiosqlite Cursor object. Phase 3 will address these endpoint migrations.

2026-03-03 - Phase 3: Endpoint Optimization Completed
Context: Refactored individual endpoints (`/v1/evaluate/{category}`, `/v1/recommend`, `/v1/rankings`) to use `aiosqlite` and `await` their database operations.
Learning: Converting the dependency injection to async and removing the synchronous bottleneck completely unlocked the application.
Evidence: 500 total requests at 50 concurrency. 500 requests completed (0 errors).
Baseline Throughput: ~87 req/sec (100% error rate on DB).
Phase 3 Throughput: ~320 req/sec (0% error rate).
Action: The foundation is now highly concurrent and thread-safe. Phase 4 will implement an application-level caching layer to further protect the database from read-heavy loads (`/v1/rankings` and `/v1/recommend`) as those operations grow more complex.

2026-03-03 - Phase 4: Application Caching Added
Context: Added `TTLCache`, a lightweight asynchronous, thread-safe memory cache. Applied it to the `/v1/recommend` and `/v1/rankings` endpoints.
Learning: By introducing `asyncio.Lock()`, cache writes and reads are safe under high concurrency.
Evidence: 500 total requests at 50 concurrency.
Throughput: ~306-320 req/sec (0 errors).
Latency improvements will be significantly more pronounced once the mock data generation is replaced by true `aiosqlite` complex queries or Ollama LLM inferences in the future. The cache shields those heavier underlying operations.
Action: Foundation optimization complete. System is stable under load, thread-safe, and defensively cached for read operations.
