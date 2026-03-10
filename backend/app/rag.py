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

import json
import logging
import os
import pathlib

import numpy as np
import requests
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from app import db
from app.models import StrategyEmbedding

logger = logging.getLogger("StudyBot")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
USE_RAG_STRATEGY = os.getenv("USE_RAG_STRATEGY", "false").lower() == "true"
RAG_EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_BASE_URL = os.getenv("BASE_URL", "http://localhost:11434").rstrip("/")

_CONFIG_DIR = pathlib.Path(__file__).resolve().parent.parent / "config"
_STRATEGIES_PATH = _CONFIG_DIR / "learning_strategies.json"
_CODE_MAP_PATH = _CONFIG_DIR / "strategy_code_map.json"

# Reverse map: rag_id → interview_id  (e.g. "rehearsal_mnemonics" → "001-001")
_RAG_TO_INTERVIEW: dict[str, str] = {}


def _load_code_map() -> dict[str, str]:
    """Load and invert the code map so we can translate RAG IDs back."""
    global _RAG_TO_INTERVIEW
    if _RAG_TO_INTERVIEW:
        return _RAG_TO_INTERVIEW
    with open(_CODE_MAP_PATH, "r", encoding="utf-8") as f:
        code_map = json.load(f)  # {"001-001": "rehearsal_mnemonics", ...}
    _RAG_TO_INTERVIEW = {v: k for k, v in code_map.items()}
    return _RAG_TO_INTERVIEW


# ---------------------------------------------------------------------------
# Ollama embeddings
# ---------------------------------------------------------------------------

def _get_embedding(text: str) -> list[float]:
    """Call Ollama's embedding endpoint and return the vector."""
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/embeddings",
        json={"model": RAG_EMBEDDING_MODEL, "prompt": text},
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    if "embedding" not in data:
        raise ValueError(f"Unexpected Ollama embedding response: {data}")
    return data["embedding"]


# ---------------------------------------------------------------------------
# Strategy text builder  (mirrors RAG/embed_strategies.py)
# ---------------------------------------------------------------------------

def _build_strategy_text(strategy: dict) -> str:
    """Build a semantically rich text for embedding a strategy."""
    parts = [f"Learning strategy: {strategy['name']}"]

    if "definitions" in strategy:
        parts.append(" ".join(strategy["definitions"]) * 2)
    if "student_phrases" in strategy:
        parts.append(" ".join(strategy["student_phrases"]) * 3)
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

    existing_count = db.session.scalar(
        sa.select(sa.func.count()).select_from(StrategyEmbedding)
    )

    if existing_count and existing_count >= len(strategies):
        logger.info(
            "[RAG] strategy_embedding already contains %d rows — skipping seed.",
            existing_count,
        )
        return

    logger.info("[RAG] Seeding %d strategy embeddings via %s …",
                len(strategies), RAG_EMBEDDING_MODEL)

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
        {"vec": str(query_vector.tolist()), "k": top_k},
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
