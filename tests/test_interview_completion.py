"""
Interview completion integration test.

Simulates a complete interview end-to-end via the Flask test client:
  POST /startConversation  → bot greeting
  POST /reply (loop)       → drives interview through all steps until
                             the backend signals completion

The "answer script" uses fixed, realistic replies that should trigger:
  • intro   : student names a study subject
  • strategy: mentions at least one learning strategy per context
  • frequency: provides a numeric rating

Stats printed at the end:
  - total turns taken
  - HTTP status codes seen
  - conversation steps visited
  - whether interview_completed flag is True in DB

Usage
-----
    cd backend
    poetry run pytest ../tests/test_interview_completion.py -v -s
"""

import json
import pathlib
import sys
import time
import pytest

BACKEND_DIR = pathlib.Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import app as flask_app_instance, db as _db  # noqa: E402
from app.database.crud import get_user                 # noqa: E402

# ---------------------------------------------------------------------------
# Test user
# ---------------------------------------------------------------------------
TEST_USER = "test_interview_bot"
TEST_CLIENT = "standalone"
TEST_LANG = "en"

# ---------------------------------------------------------------------------
# Answer selection
# Chooses a reply based on what the bot just asked.
# ---------------------------------------------------------------------------

# Keywords that indicate a frequency/quantity question
_FREQUENCY_KEYWORDS = [
    "how often", "wie oft", "frequency", "scale", "rarely", "sometimes",
    "seldom", "rating", "rate", "1 (", "1 =", "1=", "(1)", "scale of 1",
    "on a scale", "auf einer skala", "how frequently", "how much",
]

# Canned strategy answers — cycled through for strategy questions
_STRATEGY_ANSWERS = [
    "I usually summarize the key points and create flashcards to memorize them.",
    "I read the material multiple times and highlight the most important passages.",
    "I practice with old exam questions and try to explain concepts out loud to myself.",
    "I make mind maps and group related topics together to see the big picture.",
    "I work through exercises repeatedly until I feel confident with the material.",
    "I set a fixed study schedule and take regular breaks to stay focused.",
    "I discuss the topics with fellow students and ask my lecturer questions.",
    "I look up additional sources and cross-reference what I've learned with the textbook.",
    "I write detailed summaries after each lecture and review them the following day.",
    "I use the Pomodoro technique to structure my study sessions with short breaks.",
    "I create concept maps to link ideas and identify gaps in my understanding.",
    "I test myself with practice questions before the exam to check what I still need to learn.",
]
_strategy_answer_idx = 0

MAX_TURNS = 80       # safety cap; a normal interview takes ~5–15 turns
SLEEP_BETWEEN = 0    # seconds to wait between turns (0 = no delay)


def _choose_answer(bot_message: str) -> str:
    """Return a number 1-4 for frequency questions, a strategy description otherwise."""
    global _strategy_answer_idx
    msg_lower = (bot_message or "").lower()

    if any(kw in msg_lower for kw in _FREQUENCY_KEYWORDS):
        return "3"  # "often" — always a valid rating

    answer = _STRATEGY_ANSWERS[_strategy_answer_idx % len(_STRATEGY_ANSWERS)]
    _strategy_answer_idx += 1
    return answer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    flask_app_instance.config["TESTING"] = True
    with flask_app_instance.app_context():
        _db.create_all()
        # Clean up leftover test user from previous runs
        user = get_user(TEST_USER, TEST_CLIENT)
        if user:
            from app.core import reset_conversation
            reset_conversation(user)
        yield flask_app_instance.test_client()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _post(client, path: str, payload: dict) -> tuple[int, dict | str]:
    resp = client.post(
        path,
        data=json.dumps(payload),
        content_type="application/json",
    )
    try:
        data = json.loads(resp.data)
    except Exception:
        data = resp.data.decode()
    return resp.status_code, data


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

class TestInterviewCompletion:

    def test_full_interview(self, client):
        stats = {
            "turns": 0,
            "status_codes": [],
            "steps_seen": set(),
            "bot_messages": [],
            "errors": [],
        }

        # ── 1. Start conversation ────────────────────────────────────────
        status, data = _post(client, "/startConversation", {
            "language": TEST_LANG,
            "client": TEST_CLIENT,
            "userid": TEST_USER,
        })
        stats["status_codes"].append(status)
        assert status == 200, f"/startConversation returned {status}: {data}"

        greeting = data.get("message") if isinstance(data, dict) else data
        stats["bot_messages"].append(f"[START] {greeting}")
        print(f"\n[BOT] {greeting}")

        # ── 2. Reply loop ────────────────────────────────────────────────
        last_bot_msg = greeting  # seed with the greeting for first answer choice
        interview_done = False

        with flask_app_instance.app_context():
            for turn in range(MAX_TURNS):
                # intro turn: always name a subject
                if turn == 0:
                    answer = "I'm studying Computer Science."
                else:
                    answer = _choose_answer(last_bot_msg)

                print(f"\n[USER turn {turn + 1}] {answer}")

                status, data = _post(client, "/reply", {
                    "message": answer,
                    "client": TEST_CLIENT,
                    "userid": TEST_USER,
                })
                stats["turns"] += 1
                stats["status_codes"].append(status)

                if status != 200:
                    msg = data.get("message") if isinstance(data, dict) else data
                    stats["errors"].append(f"Turn {turn + 1}: HTTP {status} – {msg}")
                    print(f"  [ERROR] HTTP {status}: {msg}")
                    # Don't abort — keep track and continue to see if it recovers
                    continue

                bot_msg = data.get("message") if isinstance(data, dict) else data
                stats["bot_messages"].append(f"[T{turn + 1}] {bot_msg}")
                print(f"[BOT] {bot_msg}")
                last_bot_msg = bot_msg or ""

                # Check DB state
                user = get_user(TEST_USER, TEST_CLIENT)
                assert user is not None
                step = user.conversation_state.current_conversation_step
                stats["steps_seen"].add(step)

                if user.conversation_state.interview_completed:
                    interview_done = True
                    print(f"\n✓ Interview marked completed after {turn + 1} turns")
                    break

                if step == "complete":
                    interview_done = True
                    print(f"\n✓ Reached 'complete' step after {turn + 1} turns")
                    break

                if SLEEP_BETWEEN:
                    time.sleep(SLEEP_BETWEEN)

        # ── 3. Print stats ───────────────────────────────────────────────
        print("\n" + "=" * 60)
        print("INTERVIEW COMPLETION TEST — STATS")
        print("=" * 60)
        print(f"  Total turns taken : {stats['turns']}")
        print(f"  Max turns allowed : {MAX_TURNS}")
        print(f"  Steps visited     : {sorted(stats['steps_seen'])}")
        print(f"  Status codes seen : {sorted(set(stats['status_codes']))}")
        print(f"  Errors            : {len(stats['errors'])}")
        for e in stats["errors"]:
            print(f"    • {e}")
        print(f"  Interview done    : {interview_done}")
        print("=" * 60)

        assert interview_done, (
            f"Interview did NOT complete within {MAX_TURNS} turns. "
            f"Last step: {sorted(stats['steps_seen'])[-1] if stats['steps_seen'] else 'unknown'}. "
            f"Errors: {stats['errors']}"
        )
        assert len(stats["errors"]) == 0, f"Errors occurred during interview: {stats['errors']}"
