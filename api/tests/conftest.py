"""
Shared pytest fixtures for strategy-detection tests.

These are **integration tests** that require:
  • a running PostgreSQL database (same as the dev DB)
  • a running Ollama instance with ``nomic-embed-text`` (for RAG tests)
  • a running Ollama instance with ``phi3:latest``    (for LLM tests)

Usage
-----
    cd api
    poetry run pytest tests/ -v              # all tests
    poetry run pytest tests/ -v -k rag       # RAG tests only
    poetry run pytest tests/ -v -k llm       # LLM tests only
    poetry run pytest tests/ -v --timeout=0  # no timeout (for slow LLM tests)
"""

import os
import sys
import csv
import json
import pathlib

import pytest

# Ensure api/ is importable
API_DIR = pathlib.Path(__file__).resolve().parent.parent
if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

# Force RAG on for tests (so seeding runs)
os.environ.setdefault("USE_RAG_STRATEGY", "true")

from app import app, db as _db                       # noqa: E402
from app.rag import seed_strategy_embeddings          # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def flask_app():
    """Create the Flask application and push an app context for the entire
    test session.  Seeds RAG embeddings once."""
    app.config["TESTING"] = True
    with app.app_context():
        _db.create_all()
        seed_strategy_embeddings()
        yield app


@pytest.fixture(scope="session")
def db(flask_app):
    """Return the SQLAlchemy db instance (already inside an app context)."""
    return _db


# ---------------------------------------------------------------------------
# Eval dataset loader
# ---------------------------------------------------------------------------

_EVAL_CSV = pathlib.Path(__file__).resolve().parent / "strategy_eval.csv"
_CODE_MAP = API_DIR / "app" / "config" / "strategy_code_map.json"


def _load_code_map() -> dict[str, str]:
    with open(_CODE_MAP, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_eval_conversations() -> list[dict]:
    """
    Parse strategy_eval.csv into per-participant conversation windows.

    For every row that has a ``gold_strategy`` label we collect the
    preceding conversation turns (same participant) as context and bundle
    them into a test case dict::

        {
            "participant": "P1",
            "conversation": ["msg1", "msg2", ...],
            "gold_strategy": "004-002",
            "gold_strategy_id": "organization",
        }

    To keep the test suite feasible we use the **last 6 messages** leading
    up to (and including) the labeled row as the conversation window — the
    same window size that ``detect_strategies_rag()`` uses.
    """
    code_map = _load_code_map()

    conversations: dict[str, list[str]] = {}   # participant → cumulative msgs
    cases: list[dict] = []

    with open(_EVAL_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            participant = row["participant"].strip()
            message = row["message"].strip()
            gold = row["gold_strategy"].strip()

            conversations.setdefault(participant, []).append(message)

            if gold and gold != "nan":
                window = conversations[participant][-6:]
                cases.append({
                    "participant": participant,
                    "conversation": list(window),
                    "gold_strategy": gold,
                    "gold_strategy_id": code_map.get(gold, gold),
                })

    return cases


# Cache so parametrize can access it at collection time
EVAL_CASES = _load_eval_conversations()


def short_id(case: dict) -> str:
    """Short pytest ID like ``P1-004-002[3]``."""
    return f"{case['participant']}-{case['gold_strategy']}"
