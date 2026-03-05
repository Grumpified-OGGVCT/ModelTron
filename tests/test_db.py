import sqlite3
import os
from main import init_db

def test_schema_creation():
    if os.path.exists("data/rankings.db"):
        os.remove("data/rankings.db")
    init_db()

    conn = sqlite3.connect("data/rankings.db")
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    assert "models" in tables
    assert "evaluations" in tables
    assert "cache" in tables

    conn.close()
