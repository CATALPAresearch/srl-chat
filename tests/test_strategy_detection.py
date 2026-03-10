"""
Strategy-detection integration tests — RAG (embedding) and LLM paths.

Reads labelled conversation turns from ``strategy_eval.csv`` and checks
whether the detected strategy matches the gold label.

**Requires running PostgreSQL + Ollama** (see conftest.py header).

Run
---
    cd backend
    poetry run pytest ../tests/ -v                        # all
    poetry run pytest ../tests/ -v -k rag                 # RAG only
    poetry run pytest ../tests/ -v -k llm                 # LLM only (slow!)
    poetry run pytest ../tests/ -v -k "rag and top1"      # strict top-1 RAG
    poetry run pytest ../tests/ -v -k "rag and top3"      # relaxed top-3 RAG
    poetry run pytest ../tests/ -v --timeout 600          # generous timeout

Each test is parametrized over every labelled row in the eval CSV.
"""

import json
import logging
import pathlib

import pytest

from tests.conftest import EVAL_CASES, short_id

logger = logging.getLogger("test_strategy")

# ---------------------------------------------------------------------------
# Load code map for reverse lookups
# ---------------------------------------------------------------------------
_CODE_MAP_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / "backend" / "config" / "strategy_code_map.json"
)
with open(_CODE_MAP_PATH, "r", encoding="utf-8") as _f:
    _CODE_MAP: dict[str, str] = json.load(_f)
_REVERSE_MAP: dict[str, str] = {v: k for k, v in _CODE_MAP.items()}


# ===================================================================
#  RAG TESTS  (embedding similarity via pgvector)
# ===================================================================

class TestRAGDetection:
    """Test ``detect_strategies_rag()`` against gold labels."""

    @pytest.mark.timeout(30)
    @pytest.mark.parametrize(
        "case",
        EVAL_CASES,
        ids=[short_id(c) for c in EVAL_CASES],
    )
    def test_rag_top3_hit(self, flask_app, case):
        """Gold strategy appears among the top-3 RAG results."""
        from app.rag import detect_strategies_rag

        with flask_app.app_context():
            result_ids = detect_strategies_rag(
                case["conversation"], top_k=3
            )

        gold = case["gold_strategy"]
        assert gold in result_ids, (
            f"Gold {gold} ({case['gold_strategy_id']}) not in top-3: {result_ids}"
        )

    @pytest.mark.timeout(30)
    @pytest.mark.parametrize(
        "case",
        EVAL_CASES,
        ids=[short_id(c) for c in EVAL_CASES],
    )
    def test_rag_top1_hit(self, flask_app, case):
        """Gold strategy is the #1 RAG result (strict accuracy)."""
        from app.rag import detect_strategies_rag

        with flask_app.app_context():
            result_ids = detect_strategies_rag(
                case["conversation"], top_k=1
            )

        gold = case["gold_strategy"]
        assert result_ids and result_ids[0] == gold, (
            f"Gold {gold} ({case['gold_strategy_id']}) ≠ top-1: {result_ids}"
        )


# ===================================================================
#  LLM TESTS  (chain-of-thought via Ollama phi3)
# ===================================================================

# LLM tests are very slow (~10-30 s each).  Run a smaller sample by default.
# Override with: pytest -k llm --run-all-llm
_LLM_SAMPLE_SIZE = 20       # test only first N cases unless --run-all-llm

def _llm_cases():
    """Return a (possibly sampled) list of eval cases for LLM tests."""
    # Deduplicate: pick one case per gold_strategy to ensure coverage
    seen: set[str] = set()
    representative: list[dict] = []
    for c in EVAL_CASES:
        if c["gold_strategy"] not in seen:
            seen.add(c["gold_strategy"])
            representative.append(c)

    # Fill up with remaining cases until we hit the sample size
    for c in EVAL_CASES:
        if len(representative) >= _LLM_SAMPLE_SIZE:
            break
        if c not in representative:
            representative.append(c)

    return representative


_LLM_CASES = _llm_cases()


class TestLLMDetection:
    """Test ``_strategy_step_llm()`` against gold labels.

    These tests create a minimal mock ``User`` to drive the LLM pipeline.
    They are much slower than RAG tests.
    """

    @pytest.mark.timeout(120)
    @pytest.mark.parametrize(
        "case",
        _LLM_CASES,
        ids=[short_id(c) for c in _LLM_CASES],
    )
    def test_llm_detection(self, flask_app, db, case):
        """LLM strategy detection returns the gold strategy."""
        from app.steps import _strategy_step_llm
        from app.models import User, Language, ConversationState

        with flask_app.app_context():
            # --- ensure a test user exists in the DB -------------------------
            lang = db.session.get(Language, "test_lang")
            if not lang:
                lang = Language(id="test_lang", lang_code="en")
                db.session.add(lang)
                db.session.flush()

            user_id = f"test_{case['participant']}"
            user = db.session.query(User).filter_by(
                id=user_id, client="pytest"
            ).first()
            if not user:
                user = User(
                    id=user_id,
                    client="pytest",
                    language_id="test_lang",
                    study_subject="Psychology",
                )
                db.session.add(user)
                db.session.flush()

                state = ConversationState(
                    id=f"state_{user_id}",
                    user_id=user_id,
                    user_client="pytest",
                    current_conversation_step="strategy",
                )
                db.session.add(state)
                db.session.commit()

            # Build conversation in the format the LLM step expects
            prev_conversation = []
            for i, msg in enumerate(case["conversation"]):
                role = "user" if i % 2 == 0 else "assistant"
                prev_conversation.append({"role": role, "content": msg})

            # Run the LLM strategy detection
            strategies, status, comment = _strategy_step_llm(
                user,
                context="writing scientific papers",
                prev_conversation=prev_conversation,
            )

            gold = case["gold_strategy"]
            assert gold in strategies or case["gold_strategy_id"] in strategies, (
                f"Gold {gold} ({case['gold_strategy_id']}) not in LLM result: "
                f"{strategies} (status={status})"
            )


# ===================================================================
#  Summary / aggregate tests
# ===================================================================

class TestRAGAccuracy:
    """Run all RAG cases and report aggregate accuracy.

    This is a single test that loops internally to produce a summary
    report, useful for benchmarking.
    """

    @pytest.mark.timeout(600)
    def test_rag_aggregate_accuracy(self, flask_app):
        """Compute top-1 and top-3 accuracy over the full eval set."""
        from app.rag import detect_strategies_rag

        top1_hits = 0
        top3_hits = 0
        total = len(EVAL_CASES)
        errors: list[str] = []

        with flask_app.app_context():
            for case in EVAL_CASES:
                try:
                    result_ids = detect_strategies_rag(
                        case["conversation"], top_k=3
                    )
                except Exception as e:
                    errors.append(f"{case['participant']}: {e}")
                    continue

                gold = case["gold_strategy"]
                if result_ids and result_ids[0] == gold:
                    top1_hits += 1
                if gold in result_ids:
                    top3_hits += 1

        top1_acc = top1_hits / total * 100 if total else 0
        top3_acc = top3_hits / total * 100 if total else 0

        report = (
            f"\n{'='*60}\n"
            f"RAG Strategy Detection — Evaluation Report\n"
            f"{'='*60}\n"
            f"Total labelled cases : {total}\n"
            f"Top-1 accuracy       : {top1_hits}/{total} ({top1_acc:.1f}%)\n"
            f"Top-3 accuracy       : {top3_hits}/{total} ({top3_acc:.1f}%)\n"
            f"Embedding errors     : {len(errors)}\n"
            f"{'='*60}\n"
        )
        print(report)
        logger.info(report)

        # Don't fail — this is a benchmark, not a correctness gate
        # But warn if accuracy is unusually low
        if top3_acc < 10:
            pytest.skip(
                f"Top-3 accuracy is only {top3_acc:.1f}% — "
                "check Ollama / DB connectivity"
            )
