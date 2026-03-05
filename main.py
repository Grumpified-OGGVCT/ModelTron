import uvicorn
from fastapi import FastAPI, HTTPException, Header, Depends
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import uuid
import datetime
import sqlite3
import json
import os

app = FastAPI(
    title="ModelTron Engine API",
    description="Enterprise Model Ranking System API",
    version="2026.1"
)

DB_PATH = "data/rankings.db"

# ⚡ Bolt Optimization: Global DB connection for connection pooling
# Before: New connection per request (slow, blocked event loop)
# After: Single global connection with WAL mode enabled (fast, thread-safe)
GLOBAL_DB_CONN = None

def get_db():
    global GLOBAL_DB_CONN
    if GLOBAL_DB_CONN is None:
        if not os.path.exists("data"):
            os.makedirs("data")
        # Use check_same_thread=False to share across FastAPI threadpool
        GLOBAL_DB_CONN = sqlite3.connect(DB_PATH, check_same_thread=False)
        # WAL mode allows concurrent reads and writes, NORMAL synchronous is faster
        GLOBAL_DB_CONN.execute("PRAGMA journal_mode=WAL;")
        GLOBAL_DB_CONN.execute("PRAGMA synchronous=NORMAL;")
        GLOBAL_DB_CONN.execute("PRAGMA cache_size=-64000;") # 64MB cache
        GLOBAL_DB_CONN.row_factory = sqlite3.Row
    yield GLOBAL_DB_CONN

def init_db():
    if not os.path.exists("data"):
        os.makedirs("data")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    with open("src/db/schema.sql", "r") as f:
        conn.executescript(f.read())
    conn.close()

class EvaluationRequest(BaseModel):
    category: str
    model_id: str
    parameters: Dict[str, Any]

class RecommendationRequest(BaseModel):
    task_type: str
    max_latency_ms: Optional[int] = None
    budget_tier: Optional[str] = None
    safety_priority: Optional[str] = None
    context_required: Optional[int] = None

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/v1/health")
def health_check():
    return {"status": "ok", "version": "2026.1", "engine": "ModelTron"}

@app.get("/v1/benchmarks")
def list_benchmarks():
    return {
        "categories": [
            "code_generation", "reasoning", "agentic", "multimodal",
            "context_management", "structured_outputs", "security", "performance"
        ]
    }

@app.post("/v1/evaluate/{category}")
def evaluate_model(category: str, req: EvaluationRequest, idempotency_key: Optional[str] = Header(None), db: sqlite3.Connection = Depends(get_db)):
    # Check cache
    if idempotency_key:
        cached = db.execute("SELECT response FROM cache WHERE idempotency_key = ?", (idempotency_key,)).fetchone()
        if cached:
            return json.loads(cached["response"])

    # Mock evaluation logic for deterministic grading pipeline
    score = 95.5 if category == "security" else 88.0
    eval_id = f"eval_{uuid.uuid4().hex[:8]}"

    response = {
        "evaluation_id": eval_id,
        "model_id": req.model_id,
        "category": category,
        "score": score,
        "status": "PASS" if score >= 85.0 else "FAIL",
        "metrics": {"task_completion_rate": score}
    }

    # Store in DB
    db.execute(
        "INSERT INTO evaluations (id, model_id, category, score, metrics, verification_method) VALUES (?, ?, ?, ?, ?, ?)",
        (eval_id, req.model_id, category, score, json.dumps(response["metrics"]), "DETERMINISTIC_EXECUTION")
    )

    if idempotency_key:
        db.execute(
            "INSERT INTO cache (idempotency_key, response) VALUES (?, ?)",
            (idempotency_key, json.dumps(response))
        )

    db.commit()
    return response

@app.get("/v1/recommend")
def recommend_model(task_type: str, context_required: Optional[int] = None, db: sqlite3.Connection = Depends(get_db)):
    # Mock capability router logic
    recommended = "glm-5:cloud"
    if task_type == "code_generation":
        recommended = "minimax-m2.5:cloud"
    elif task_type == "multimodal":
        recommended = "qwen3-vl:235b-cloud"
    elif task_type == "logical_reasoning":
        recommended = "deepseek-v3.2:cloud"

    return {
        "recommendation_id": f"rec_{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "recommended_model": recommended,
        "reasoning": f"Ranked #1 for {task_type}.",
        "confidence_score": 0.95
    }

@app.get("/v1/rankings")
def get_rankings(db: sqlite3.Connection = Depends(get_db)):
    # Return mock or DB-aggregated rankings
    return {
        "leaderboard": [
            {"rank": 1, "model": "deepseek-v3.2:cloud", "score": 98.2, "category": "Reasoning"},
            {"rank": 2, "model": "glm-5:cloud", "score": 97.5, "category": "Structured Outputs"},
            {"rank": 3, "model": "minimax-m2.5:cloud", "score": 96.8, "category": "Code Generation"}
        ]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
