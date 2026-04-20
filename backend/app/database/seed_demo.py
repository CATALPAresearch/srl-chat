"""
Seed the database with demo students so the radar chart and course average are visible.

Usage (from backend/):
    poetry run python -m app.database.seed_demo
"""
import uuid

import sqlalchemy as sa

from app import app, db
from app.database.crud import get_language
from app.models import (
    ConversationState, Context, InterviewAnswer, User, UserStrategy,
)

app.app_context().push()

CLIENT = "standalone"
LANG   = "en"

# ── Frequency profiles: code → frequency (0 = not mentioned) ──────────
# Scale: 1=seldom, 2=sometimes, 3=often, 4=most of the time
DEMO_STUDENTS = [
    {
        "id": "demo_student",
        "subject": "Computer Science",
        "freqs": {
            "001-001": 4, "001-002": 3, "002-001": 2, "003-001": 4,
            "004-001": 3, "004-002": 2, "004-003": 3, "005-002": 1,
            "006-001": 2, "006-002": 1, "007-005": 3,
        },
    },
    {
        "id": "peer_student_1",
        "subject": "Computer Science",
        "freqs": {
            "001-001": 2, "001-002": 4, "002-001": 3, "003-001": 2,
            "004-001": 4, "004-002": 3, "005-001": 2, "006-001": 3,
            "006-002": 2, "007-001": 1, "007-005": 4,
        },
    },
    {
        "id": "peer_student_2",
        "subject": "Computer Science",
        "freqs": {
            "001-002": 2, "002-001": 4, "004-001": 2, "004-003": 3,
            "004-004": 2, "005-002": 3, "006-001": 4, "006-002": 3,
            "007-003": 2, "007-005": 2,
        },
    },
    {
        "id": "peer_student_3",
        "subject": "Computer Science",
        "freqs": {
            "001-001": 3, "001-002": 3, "003-001": 3, "004-001": 4,
            "004-002": 4, "005-001": 3, "006-001": 2, "007-003": 3,
            "007-004": 2, "007-005": 3,
        },
    },
    {
        "id": "peer_student_4",
        "subject": "Computer Science",
        "freqs": {
            "001-001": 1, "002-001": 1, "004-001": 2, "004-003": 1,
            "006-001": 1, "007-005": 2,
        },
    },
    {
        "id": "peer_student_5",
        "subject": "Computer Science",
        "freqs": {
            "001-001": 4, "001-002": 4, "002-001": 4, "003-001": 3,
            "004-001": 4, "004-002": 3, "004-003": 4, "005-001": 4,
            "005-002": 3, "006-001": 4, "006-002": 4,
            "007-001": 2, "007-005": 4,
        },
    },
]

# ── Helpers ────────────────────────────────────────────────────────────
lang_db = get_language(LANG)
if not lang_db:
    raise SystemExit(f"Language '{LANG}' not found. Run setup_no_embed first.")

context = db.session.scalar(
    sa.select(Context).where(Context.language_id == lang_db.id)
)
if not context:
    raise SystemExit("No contexts found. Run setup_no_embed first.")


def seed_student(uid, subject, freqs):
    # Remove if exists
    existing = db.session.scalar(
        sa.select(User).where(User.id == uid).where(User.client == CLIENT)
    )
    if existing:
        db.session.delete(existing)
        db.session.commit()

    user = User(id=uid, client=CLIENT, language_id=lang_db.id, study_subject=subject)
    db.session.add(user)
    db.session.flush()

    conv = ConversationState(
        id=str(uuid.uuid4()),
        user_id=uid,
        user_client=CLIENT,
        current_turn=6,
        current_conversation_step="complete",
        interview_completed=True,
    )
    db.session.add(conv)
    db.session.flush()

    for code, freq in freqs.items():
        answer = InterviewAnswer(
            id=str(uuid.uuid4()),
            user_id=uid,
            user_client=CLIENT,
            context=context.id,
            strategy=code,
            turn=1,
            message="[seed]",
            conversation_step="frequency",
        )
        db.session.add(answer)
        db.session.flush()

        db.session.add(UserStrategy(
            id=str(uuid.uuid4()),
            user_id=uid,
            user_client=CLIENT,
            interview_answer_id=answer.id,
            context=context.id,
            strategy=code,
            frequency=freq,
        ))

    db.session.commit()
    print(f"  Seeded '{uid}' with {len(freqs)} strategies.")


for student in DEMO_STUDENTS:
    seed_student(student["id"], student["subject"], student["freqs"])

print(f"\nDone. {len(DEMO_STUDENTS)} students in client='{CLIENT}'.")
print("Demo view: ?userid=demo_student&client=standalone")
