import os
import numpy as np
import requests
import psycopg2
from pgvector.psycopg2 import register_vector

# -----------------------------
# OLLAMA CONFIG (LOCAL)
# -----------------------------
OLLAMA_BASE_URL = os.getenv("BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# -----------------------------
# DATABASE CONFIG
# -----------------------------
DB_CONN = "postgresql://chat:example@localhost:5432/srl_chat"

# -----------------------------
# EMBEDDING FUNCTION (OLLAMA)
# -----------------------------
def get_embedding(text: str) -> list[float]:
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


# -----------------------------
# RETRIEVAL FUNCTION
# -----------------------------
def get_top3_similar_strategies(query_text: str, connection):
    embedding = np.array(get_embedding(query_text), dtype=np.float32)

    register_vector(connection)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT strategy_id, name, phase
        FROM strategy_embedding
        ORDER BY embedding <=> %s
        LIMIT 3;
    """, (embedding,))

    return cursor.fetchall()


# -----------------------------
# TEST QUERY
# -----------------------------
if __name__ == "__main__":
    conn = psycopg2.connect(DB_CONN)

    user_input = (
        "I usually summarize my notes, make mind maps, "
        "and study in short focused sessions with breaks."
    )

    results = get_top3_similar_strategies(user_input, conn)

    print("Detected learning strategies:")
    for r in results:
        print(f"- {r[1]} (id={r[0]}, phase={r[2]})")

    conn.close()
