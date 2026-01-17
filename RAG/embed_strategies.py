import json
import os
import requests
import psycopg2
import numpy as np
from pgvector.psycopg2 import register_vector

# -----------------------------
# OLLAMA CONFIG (NO AUTH NEEDED)
# -----------------------------
OLLAMA_BASE_URL = os.getenv("BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

DB_CONN = "postgresql://chat:example@localhost:5432/srl_chat"


def embed(text: str) -> list[float]:
    """Get embeddings from Ollama"""
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={
            "model": OLLAMA_MODEL,
            "prompt": text
        },
        timeout=60
    )

    response.raise_for_status()
    data = response.json()

    if "embedding" not in data:
        raise ValueError(f"Unexpected Ollama response: {data}")

    return data["embedding"]


def build_strategy_text(strategy: dict) -> str:
    parts = [
        f"Strategy: {strategy['name']}",
        f"Definitions: {' '.join(strategy['definitions'])}",
        f"Synonyms: {' '.join(strategy['synonyms'])}",
        f"Methods: {' '.join(strategy['methods'])}",
        f"Indicators: {' '.join(strategy['positive_indicators'])}"
    ]
    return "\n".join(parts)


# -----------------------------
# LOAD STRATEGIES
# -----------------------------
with open("learning_strategies.json", "r", encoding="utf-8") as f:
    strategies = json.load(f)

# -----------------------------
# DATABASE SETUP
# -----------------------------
conn = psycopg2.connect(DB_CONN)
register_vector(conn)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS strategy_embedding (
    strategy_id TEXT PRIMARY KEY,
    name TEXT,
    phase TEXT,
    category TEXT,
    content TEXT,
    embedding VECTOR(768)
);
""")
conn.commit()

# -----------------------------
# EMBED + STORE
# -----------------------------
for s in strategies:
    text = build_strategy_text(s)
    vector = np.array(embed(text), dtype=np.float32)

    cur.execute("""
        INSERT INTO strategy_embedding
        (strategy_id, name, phase, category, content, embedding)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (strategy_id) DO UPDATE SET
        content = EXCLUDED.content,
        embedding = EXCLUDED.embedding;
    """, (
        s["strategy_id"],
        s["name"],
        s["zimmerman_phase"],
        s["category"],
        text,
        vector
    ))

conn.commit()
cur.close()
conn.close()

print(" Strategy embeddings created successfully using Ollama.")
