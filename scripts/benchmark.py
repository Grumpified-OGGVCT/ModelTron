import asyncio
import httpx
import time
import statistics
import sys
from collections import defaultdict

BASE_URL = "http://127.0.0.1:8000"
CONCURRENCY = 50
TOTAL_REQUESTS = 500

async def fetch(client: httpx.AsyncClient, method: str, path: str, json_data: dict = None, headers: dict = None) -> float:
    start_time = time.perf_counter()
    try:
        if method == "GET":
            response = await client.get(f"{BASE_URL}{path}", headers=headers)
        elif method == "POST":
            response = await client.post(f"{BASE_URL}{path}", json=json_data, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"Request failed: {e}")
        return 0.0
    end_time = time.perf_counter()
    return (end_time - start_time) * 1000  # ms

async def worker(client: httpx.AsyncClient, queue: asyncio.Queue, results: list):
    while True:
        task = await queue.get()
        if task is None:
            queue.task_done()
            break

        method, path, json_data, headers = task
        latency = await fetch(client, method, path, json_data, headers)
        if latency > 0:
            results.append((path, latency))

        queue.task_done()

async def run_benchmark():
    print(f"⚡ Bolt Benchmark: Starting. Concurrency: {CONCURRENCY}, Total Requests: {TOTAL_REQUESTS}")
    queue = asyncio.Queue()
    results = []

    # Prepare tasks
    endpoints = [
        ("GET", "/v1/health", None, None),
        ("GET", "/v1/benchmarks", None, None),
        ("GET", "/v1/recommend?task_type=code_generation", None, None),
        ("GET", "/v1/rankings", None, None),
        ("POST", "/v1/evaluate/security", {
            "category": "security",
            "model_id": "glm-5:cloud",
            "parameters": {"test": "data"}
        }, None)
    ]

    for i in range(TOTAL_REQUESTS):
        # Round robin through endpoints
        endpoint = endpoints[i % len(endpoints)]
        queue.put_nowait(endpoint)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Start workers
        tasks = []
        for _ in range(CONCURRENCY):
            task = asyncio.create_task(worker(client, queue, results))
            tasks.append(task)

        start_time = time.perf_counter()
        # Wait for queue to empty
        await queue.join()

        # Stop workers
        for _ in range(CONCURRENCY):
            queue.put_nowait(None)
        await asyncio.gather(*tasks)

        end_time = time.perf_counter()

    total_time = end_time - start_time
    rps = len(results) / total_time

    # Analyze results
    latencies_by_path = defaultdict(list)
    for path, latency in results:
        # group POST paths
        if path.startswith("/v1/evaluate"):
            latencies_by_path["/v1/evaluate/{category} (POST)"].append(latency)
        elif path.startswith("/v1/recommend"):
             latencies_by_path["/v1/recommend (GET)"].append(latency)
        else:
             latencies_by_path[f"{path} (GET)"].append(latency)

    print("\n📊 --- BENCHMARK RESULTS --- 📊")
    print(f"Total Requests: {len(results)}")
    print(f"Total Time: {total_time:.2f}s")
    print(f"Throughput: {rps:.2f} req/sec\n")

    for path, lats in latencies_by_path.items():
        if not lats:
            continue
        lats.sort()
        avg = statistics.mean(lats)
        p50 = lats[len(lats)//2]
        p90 = lats[int(len(lats) * 0.90)]
        p95 = lats[int(len(lats) * 0.95)]
        p99 = lats[int(len(lats) * 0.99)]

        print(f"Endpoint: {path} ({len(lats)} requests)")
        print(f"  Avg: {avg:.2f}ms | p50: {p50:.2f}ms | p90: {p90:.2f}ms | p95: {p95:.2f}ms | p99: {p99:.2f}ms")

if __name__ == "__main__":
    try:
        asyncio.run(run_benchmark())
    except KeyboardInterrupt:
        print("\nBenchmark aborted.")
        sys.exit(1)
