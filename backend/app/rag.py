"""
RAG-based learning-strategy detection using pgvector + Ollama embeddings.

When USE_RAG_STRATEGY=true the chat uses cosine-similarity search over
pre-embedded strategy descriptions instead of multiple LLM calls.

Workflow
--------
1. On startup ``seed_strategy_embeddings()`` populates / updates the
   ``strategy_embedding`` table (runs only when the table is empty **or**
   ``learning_strategies.json`` has been modified).
2. At runtime ``detect_strategies_rag()`` embeds the user's latest
   messages, queries the top-k nearest strategies and returns their
   interview-format IDs (e.g. ``"001-001"``).
"""

import hashlib
import json
import logging
import os
import pathlib
from functools import lru_cache

import numpy as np
import requests
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from app import db
from app.models import StrategyEmbedding

logger = logging.getLogger("InterviewAgent")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_RAG_STRATEGY = os.getenv("USE_RAG_STRATEGY", "false").lower() == "true"
EXPECTED_EMBEDDING_DIM = 768  # nomic-embed-text output dimension; update if model changes

_CONFIG_DIR = pathlib.Path(__file__).resolve().parent.parent / "config"
_STRATEGIES_PATH = _CONFIG_DIR / "learning_strategies.json"
_CODE_MAP_PATH = _CONFIG_DIR / "strategy_code_map.json"
_STRATEGIES_HASH_PATH = _CONFIG_DIR / "learning_strategies.hash"

@lru_cache(maxsize=1)
def _load_code_map() -> dict[str, str]:
    """Load and invert the code map (rag_id → interview_id). Result is cached."""
    with open(_CODE_MAP_PATH, "r", encoding="utf-8") as f:
        code_map = json.load(f)  # {"001-001": "rehearsal_mnemonics", ...}
    return {v: k for k, v in code_map.items()}


# ---------------------------------------------------------------------------
# Ollama embeddings
# ---------------------------------------------------------------------------

def _get_embedding(text: str) -> list[float]:
    """Call Ollama's embedding endpoint and return the vector."""
    rag_model = os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text")
    ollama_url = os.getenv("BASE_URL", "http://localhost:11434").rstrip("/")
    response = requests.post(
        f"{ollama_url}/api/embeddings",
        json={"model": rag_model, "prompt": text},
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    if "embedding" not in data:
        raise ValueError(f"Unexpected Ollama embedding response: {data}")
    vec = data["embedding"]
    if len(vec) != EXPECTED_EMBEDDING_DIM:
        raise ValueError(
            f"Embedding dimension mismatch: expected {EXPECTED_EMBEDDING_DIM}, "
            f"got {len(vec)} (model: {rag_model!r}). "
            f"Update EXPECTED_EMBEDDING_DIM or RAG_EMBEDDING_MODEL."
        )
    return vec


# ---------------------------------------------------------------------------
# Strategy text builder  (mirrors RAG/embed_strategies.py)
# ---------------------------------------------------------------------------

def _build_strategy_text(strategy: dict) -> str:
    """Build a semantically rich text for embedding a strategy."""
    parts = [f"Learning strategy: {strategy['name']}"]

    if "definitions" in strategy:
        parts.extend(strategy["definitions"] * 2)
    if "student_phrases" in strategy:
        parts.extend(strategy["student_phrases"] * 3)
    if "methods" in strategy:
        parts.append(" ".join(strategy["methods"]))
    if "positive_indicators" in strategy:
        parts.append(" ".join(strategy["positive_indicators"]))
    if "synonyms" in strategy:
        parts.append(" ".join(strategy["synonyms"]))
    if "tools" in strategy:
        parts.append(" ".join(strategy["tools"]))

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Seeding  (called once at startup when USE_RAG_STRATEGY=true)
# ---------------------------------------------------------------------------

def seed_strategy_embeddings() -> None:
    """
    Populate the ``strategy_embedding`` table from ``learning_strategies.json``.

    Skips if the table already has rows with up-to-date content.
    """
    if not USE_RAG_STRATEGY:
        return

    with open(_STRATEGIES_PATH, "r", encoding="utf-8") as f:
        strategies = json.load(f)

    current_hash = hashlib.md5(_STRATEGIES_PATH.read_bytes()).hexdigest()
    stored_hash = (
        _STRATEGIES_HASH_PATH.read_text(encoding="utf-8").strip()
        if _STRATEGIES_HASH_PATH.exists()
        else ""
    )
    existing_count = db.session.scalar(
        sa.select(sa.func.count()).select_from(StrategyEmbedding)
    )

    if existing_count >= len(strategies) and current_hash == stored_hash:
        logger.info(
            "[RAG] strategy_embedding up to date (%d rows, hash %s) — skipping seed.",
            existing_count,
            current_hash[:8],
        )
        return

    rag_model = os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text")
    logger.info("[RAG] Seeding %d strategy embeddings via %s …",
                len(strategies), rag_model)

    for s in strategies:
        text = _build_strategy_text(s)
        vector = np.array(_get_embedding(text), dtype=np.float32)

        existing = db.session.get(StrategyEmbedding, s["strategy_id"])
        if existing:
            existing.content = text
            existing.embedding = vector
        else:
            row = StrategyEmbedding(
                strategy_id=s["strategy_id"],
                name=s["name"],
                phase=s.get("zimmerman_phase"),
                category=s.get("category"),
                content=text,
                embedding=vector,
            )
            db.session.add(row)

    db.session.commit()
    _STRATEGIES_HASH_PATH.write_text(current_hash, encoding="utf-8")
    logger.info("[RAG] Strategy embeddings seeded successfully.")


# ---------------------------------------------------------------------------
# Runtime retrieval
# ---------------------------------------------------------------------------

def detect_strategies_rag(
    conversation: list[str],
    top_k: int = 3,
    threshold: float | None = None,
) -> list[str]:
    """
    Detect learning strategies from recent conversation turns using
    embedding similarity.

    Parameters
    ----------
    conversation : list[str]
        The recent conversation messages (user turns) to analyse.
    top_k : int
        Number of closest strategies to return.
    threshold : float | None
        Optional cosine-distance threshold.  Strategies farther than this
        are discarded.  ``None`` means return the top-k regardless.

    Returns
    -------
    list[str]
        Interview-format strategy IDs (e.g. ``["001-001", "004-002"]``).
        Returns ``["008-001"]`` (other) when no match is found.
    """
    code_map = _load_code_map()

    # Combine recent user messages for a single embedding
    combined_text = " ".join(conversation[-6:])  # last 6 turns max
    query_vector = np.array(_get_embedding(combined_text), dtype=np.float32)

    # pgvector cosine distance operator  <=>
    results = db.session.execute(
        sa.text("""
            SELECT strategy_id, name,
                   embedding <=> :vec AS distance
            FROM strategy_embedding
            ORDER BY embedding <=> :vec
            LIMIT :k
        """),
        {"vec": query_vector.tolist(), "k": top_k},
    ).fetchall()

    if not results:
        logger.warning("[RAG] No strategy embeddings found — returning 'other'.")
        return ["008-001"]

    interview_ids: list[str] = []
    for strategy_id, name, distance in results:
        if threshold is not None and distance > threshold:
            continue
        iid = code_map.get(strategy_id)
        if iid:
            logger.info("[RAG] Matched %s (%s) — distance %.4f", name, iid, distance)
            interview_ids.append(iid)

    if not interview_ids:
        return ["008-001"]

    return interview_ids
