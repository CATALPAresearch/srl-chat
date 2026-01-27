import csv
import json
import psycopg2
import numpy as np
import requests
import os
from pgvector.psycopg2 import register_vector

# -----------------------------
# CONFIG
# -----------------------------
DB_CONN = "postgresql://chat:example@localhost:5432/srl_chat"

OLLAMA_BASE_URL = os.getenv("BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

EVAL_CSV = "eval/strategy_eval.csv"
CODE_MAP_PATH = "eval/strategy_code_map.json"

TOP_K = 3


# -----------------------------
# LOAD CODE MAP
# -----------------------------
with open(CODE_MAP_PATH, "r", encoding="utf-8") as f:
    CODE_MAP = json.load(f)


# -----------------------------
# EMBEDDING
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
        raise ValueError(f"Unexpected embedding response: {data}")

    return data["embedding"]


# -----------------------------
# RETRIEVAL
# -----------------------------
def retrieve_top_k(query_text, conn, k=3):
    emb = np.array(get_embedding(query_text), dtype=np.float32)

    register_vector(conn)
    cur = conn.cursor()

    cur.execute("""
        SELECT strategy_id
        FROM strategy_embedding
        ORDER BY embedding <=> %s
        LIMIT %s;
    """, (emb, k))

    return [row[0] for row in cur.fetchall()]


# -----------------------------
# EVALUATION
# -----------------------------
def evaluate():
    conn = psycopg2.connect(DB_CONN)

    total = 0
    top1_correct = 0
    top3_correct = 0
    skipped = 0

    with open(EVAL_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            message = row["message"].strip()
            raw_code = row["gold_strategy"].strip()

            # Skip unlabeled rows
            if raw_code.lower() == "nan" or not raw_code:
                continue

            # Skip unknown codes
            if raw_code not in CODE_MAP:
                skipped += 1
                continue

            gold = CODE_MAP[raw_code]

            predictions = retrieve_top_k(message, conn, TOP_K)

            # Skip if strategy not embedded yet
            if not predictions:
                skipped += 1
                continue

            total += 1

            if predictions[0] == gold:
                top1_correct += 1

            if gold in predictions:
                top3_correct += 1

    conn.close()

    print("Evaluation results")
    print("------------------")
    print(f"Evaluated samples : {total}")
    print(f"Skipped samples   : {skipped}")
    print(f"Top-1 accuracy    : {top1_correct / total:.3f}")
    print(f"Top-3 accuracy    : {top3_correct / total:.3f}")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    evaluate()
