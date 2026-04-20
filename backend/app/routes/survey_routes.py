"""Survey and student-results routes."""
import json
import os
import uuid

import sqlalchemy as sa
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

from app import app, db
from ..database.crud import get_user, get_language_by_id
from ..models import (
    SurveyResponse, UserStrategy, StrategyTranslation,
    ConversationState, Context,
)
from ._paths import CONFIG_DIR

survey_bp = Blueprint('survey', __name__)


@survey_bp.route("/survey/<survey_id>", methods=["GET"])
@cross_origin()
def get_survey(survey_id):
    """
    Return the survey definition JSON for the given survey_id.
    Query params:
        - lang: language code (en, de). If not provided, uses user's language_id.
        - userid: user ID (required if lang not provided)
        - client: client identifier (required if lang not provided)
    Default language: de
    """
    safe_name = os.path.basename(survey_id)  # prevent path traversal

    lang = request.args.get('lang')
    if not lang:
        userid = request.args.get('userid')
        client = request.args.get('client')
        if userid and client:
            user = get_user(userid, client)
            if user:
                user_lang = get_language_by_id(user.language_id)
                lang = user_lang.lang_code if user_lang else 'de'
            else:
                lang = 'de'
        else:
            lang = 'de'

    # Try language-specific file first, fall back to generic bilingual file
    path = os.path.join(CONFIG_DIR, f"survey_{safe_name}_{lang}.json")
    if not os.path.isfile(path):
        path = os.path.join(CONFIG_DIR, f"survey_{safe_name}.json")

    if not os.path.isfile(path):
        return jsonify({"error": "Survey not found"}), 404

    with open(path, "r", encoding="utf-8") as f:
        survey = json.load(f)
    return jsonify(survey), 200


@survey_bp.route("/survey/<survey_id>/submit", methods=["POST", "OPTIONS"])
@cross_origin()
def submit_survey(survey_id):
    """
    Store a completed survey.
    Expected JSON body:
    {
        "userid": "...",
        "client": "...",
        "language": "en",
        "responses": { "oase_1": 4, "oase_2": 5, ... }
    }
    """
    try:
        content = request.json
        user_id = content["userid"]
        client = content["client"]
        language = content.get("language", "en")
        responses = content["responses"]

        entry = SurveyResponse(
            id=str(uuid.uuid4()),
            survey_id=survey_id,
            user_id=user_id,
            user_client=client,
            language=language,
            responses=responses,
        )
        db.session.add(entry)
        db.session.commit()

        app.logger.info("Survey %s submitted by user %s/%s", survey_id, user_id, client)
        return jsonify({"status": "ok", "id": entry.id}), 201

    except Exception as e:
        app.logger.error("Error saving survey response: %s", e)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@survey_bp.route("/student/results", methods=["GET"])
@cross_origin()
def get_student_results():
    """
    Return interview strategies and survey responses for a single student.
    Query params: userid, client
    """
    userid = request.args.get("userid")
    client = request.args.get("client", "standalone")
    if not userid:
        return jsonify({"error": "userid required"}), 400

    user = get_user(userid, client)
    if not user:
        return jsonify({"strategies": [], "survey": None, "interview_completed": False}), 200

    user_lang = get_language_by_id(user.language_id)
    lang_id = user_lang.id if user_lang else None

    # --- Strategies mentioned by this user ---
    rows = db.session.execute(
        db.select(UserStrategy, StrategyTranslation)
        .outerjoin(
            StrategyTranslation,
            (StrategyTranslation.strategy == UserStrategy.strategy) &
            (StrategyTranslation.language_id == lang_id)
        )
        .where(UserStrategy.user_id == userid)
        .where(UserStrategy.user_client == client)
    ).all()

    strategies = []
    seen = set()
    for us, st in rows:
        if us.strategy not in seen:
            seen.add(us.strategy)
            strategies.append({
                "id": us.strategy,
                "name": st.name if st else us.strategy,
                "description": st.description if st else "",
                "frequency": us.frequency,
            })

    # --- Latest survey response ---
    survey_row = (
        SurveyResponse.query
        .filter_by(user_id=userid, user_client=client)
        .order_by(SurveyResponse.submitted_at.desc())
        .first()
    )
    survey = None
    if survey_row:
        survey = {
            "survey_id": survey_row.survey_id,
            "language": survey_row.language,
            "submitted_at": survey_row.submitted_at.isoformat() if survey_row.submitted_at else None,
            "responses": survey_row.responses,
        }

    # --- Interview completion status ---
    state = ConversationState.query.filter_by(
        user_id=userid, user_client=client
    ).first()
    interview_completed = bool(state and state.interview_completed)

    # --- Progress: completed contexts vs total contexts ---
    answers_count = len(state.completed_contexts) if state else 0
    total_contexts = (
        db.session.query(Context).filter(Context.language_id == lang_id).count()
        if lang_id else 0
    )

    # --- Radar chart data: all 17 strategies with max frequency ---
    with open(os.path.join(CONFIG_DIR, "strategy_code_map.json"), "r", encoding="utf-8") as _f:
        code_map = json.load(_f)
    with open(os.path.join(CONFIG_DIR, "learning_strategies.json"), "r", encoding="utf-8") as _f:
        _strat_list = json.load(_f)
    strategy_lookup = {
        x["strategy_id"]: {
            "name": x["name"],
            "description": x["definitions"][0] if x.get("definitions") else "",
        }
        for x in _strat_list
    }

    # Build frequency map: strategy_id → max frequency across contexts
    freq_map = {}
    for us, _st in rows:
        if us.frequency and int(us.frequency) > 0:
            freq_map[us.strategy] = max(freq_map.get(us.strategy, 0), int(us.frequency))

    # --- Course average: avg frequency per strategy ---
    completed_count = db.session.scalar(
        sa.select(sa.func.count())
        .select_from(ConversationState)
        .where(ConversationState.user_client == client)
        .where(ConversationState.interview_completed == True)
    ) or 1  # avoid divide-by-zero

    peer_rows = db.session.execute(
        sa.text("""
            SELECT us.strategy, SUM(us.frequency) AS freq_sum
            FROM user_strategy us
            JOIN state cs ON cs.user_id = us.user_id AND cs.user_client = us.user_client
            WHERE us.user_client = :client
              AND cs.interview_completed = true
              AND us.frequency > 0
            GROUP BY us.strategy
        """),
        {"client": client},
    ).all()
    avg_map = {r.strategy: round(r.freq_sum / completed_count, 2) for r in peer_rows}

    radar_data = []
    for code, sid in code_map.items():
        if code == "008-001":   # skip "other"
            continue
        info = strategy_lookup.get(sid, {})
        radar_data.append({
            "id": code,
            "code": code,
            "name": info.get("name", sid),
            "description": info.get("description", ""),
            "frequency": freq_map.get(code, 0),
            "avg_frequency": avg_map.get(code, 0),
        })

    return jsonify({
        "strategies": strategies,
        "survey": survey,
        "interview_completed": interview_completed,
        "answers_count": answers_count,
        "total_contexts": total_contexts,
        "radar_data": radar_data,
    }), 200


@survey_bp.route("/survey/<survey_id>/results", methods=["GET"])
@cross_origin()
def get_survey_results(survey_id):
    """Return all responses for a given survey (admin/research endpoint)."""
    rows = SurveyResponse.query.filter_by(survey_id=survey_id).all()
    results = [
        {
            "id": r.id,
            "user_id": r.user_id,
            "user_client": r.user_client,
            "language": r.language,
            "responses": r.responses,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
        }
        for r in rows
    ]
    return jsonify(results), 200
