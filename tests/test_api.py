import pytest
from fastapi.testclient import TestClient
from main import app
import asyncio
from main import init_db_async
import os
import sqlite3

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    if os.path.exists("data/rankings.db"):
        os.remove("data/rankings.db")
    asyncio.run(init_db_async())
    yield
    if os.path.exists("data/rankings.db"):
        os.remove("data/rankings.db")

def test_health_check():
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "2026.1", "engine": "ModelTron"}

def test_list_benchmarks():
    response = client.get("/v1/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert "categories" in data
    assert "code_generation" in data["categories"]

def test_recommend_model():
    response = client.get("/v1/recommend?task_type=code_generation")
    assert response.status_code == 200
    data = response.json()
    assert "recommended_model" in data
    assert data["recommended_model"] == "minimax-m2.5:cloud"

def test_evaluate_model():
    req_data = {
        "category": "security",
        "model_id": "glm-5:cloud",
        "parameters": {"test": "data"}
    }
    response = client.post("/v1/evaluate/security", json=req_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PASS"
    assert data["score"] == 95.5

def test_idempotency_caching():
    req_data = {
        "category": "reasoning",
        "model_id": "deepseek-v3.2:cloud",
        "parameters": {}
    }
    key = "test-idempotency-key"

    # First call
    response1 = client.post("/v1/evaluate/reasoning", json=req_data, headers={"idempotency-key": key})
    assert response1.status_code == 200
    data1 = response1.json()

    # Second call with same key
    response2 = client.post("/v1/evaluate/reasoning", json=req_data, headers={"idempotency-key": key})
    assert response2.status_code == 200
    data2 = response2.json()

    assert data1["evaluation_id"] == data2["evaluation_id"]
