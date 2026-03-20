from flask import request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
import json
import os
import uuid

from app import app, db
from .core import start_conversation_core, reply_core, reset_conversation
from .database.crud import get_user, get_language_by_id
from .actions import LogAction
from .logging_utlis import log_action
from .models import SurveyResponse

cors = CORS(app)
# FixMe: cors = CORS(app, ressources={r"/api/*": {"origin": "http://localhost:80"}})

# Directories for serving the standalone frontend
_PROJECT_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
_FRONTEND_DIR = os.path.join(_PROJECT_ROOT, 'frontend')
_CONFIG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config')
_LTI_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'lti')

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(error)
    db.session.rollback()
    with open("config/translations.json", "r", encoding="utf-8") as file:
        translations = json.load(file)
    return translations["translations"]["en"]["create_error"], 500


@app.teardown_request
def teardown_request(exception):
    if exception:
        db.session.rollback()
        app.logger.error("Caught error: %s - rolling back", exception)
    else:
        db.session.commit()
    db.session.remove()


@app.route('/')
def index():
    return send_from_directory(_FRONTEND_DIR, 'index.html')


@app.route('/frontend/<path:filename>')
def serve_frontend_assets(filename):
    """Serve frontend assets (core stubs, etc.)."""
    return send_from_directory(_FRONTEND_DIR, filename)


@app.route('/static/lti/<path:filename>')
def serve_lti_static(filename):
    """Serve LTI static assets (AMD bundle + core stubs for Moodle LTI mode)."""
    return send_from_directory(_LTI_STATIC_DIR, filename)


@app.route("/resetConversation", methods=["POST", "OPTIONS"])
@cross_origin()
def delete_message():
    try:
        content = request.json
        client = content["client"]
        userid = content["userid"]
        app.logger.info("Resetting conversation for user: %s - %s", userid, client)
        user = get_user(userid, client)
        success = reset_conversation(user)
        if success:
            return "*** Conversation has been reset. A new conversation can be started from the StudyTest server. ***", 200
        return None
    except Exception as e:
        app.logger.error("Error on reset conversation: %s - Rolling back DB changes", e)
        db.session.rollback()
        with open("config/translations.json", "r", encoding="utf-8") as file:
            translations = json.load(file)
        user = get_user(userid, client)
        if user:
            user_lang = get_language_by_id(user.language_id)
            return translations["translations"][user_lang.lang_code]["reply_error"], 200
        else:
            return translations["translations"]["en"]["create_error"], 500


@app.route("/user_language/", methods=["GET"])
@cross_origin()
def get_user_language():
    """
    Args:
        "client": "discord",
        "userid": Discord user ID
    """
    with open("config/translations.json", "r", encoding="utf-8") as file:
        translations = json.load(file)
    userid = request.args.get('userid')
    client = request.args.get('client')
    user = get_user(userid, client)
    if user:
        user_lang = get_language_by_id(user.language_id)
        return user_lang.lang_code, 200
    else:
        return translations["translations"]["en"]["create_error"], 500


@app.route("/translations/<language>", methods=["GET"])
@cross_origin()
def get_translations(language):
    with open("config/translations.json", "r", encoding="utf-8") as file:
        translations = json.load(file)
    if language in list(translations["translations"].keys()):
        return translations["translations"][language]
    else:
        return jsonify(translations["language_not_supported_message"]), 400


@app.route("/startConversation", methods=['POST'])
@cross_origin()
def start_conversation_flask():
    """
    Post request format:
    {
        "language": "en" or "de",
        "client": "discord",
        "userid": Discord user ID
    }
    """
    try:
        content = request.json
        language = content["language"]
        client = content["client"]
        userid = content["userid"]
        app.logger.info("Starting new conversation (%s) for user: %s - %s", language, userid, client)

        user = get_user(userid, client)

        log_action(
            LogAction.API_CALL_START,
            user=user if user else "new_user",
            value={"endpoint": "/startConversation", "language": language, "client": client, "userid": userid},
            http_status=200,
            turn=0,
            step="request_received",
            context="conversation_start",
            strategy="strategy_not_detected"
        )

        return start_conversation_core(language, client, userid)
    except Exception as e:
        app.logger.error("Error on start conversation: %s - Rolling back DB changes", e)
        db.session.rollback()

        log_action(
            LogAction.DB_ROLLBACK,
            value={"error": str(e)},
            http_status=500,
            step="exception_handled"
        )

        with open("config/translations.json", "r", encoding="utf-8") as file:
            translations = json.load(file)
        return translations["translations"][language]["create_error"], 500


@app.route("/reply", methods=['POST'])
@cross_origin()
def reply():
    """
    Post request format:
    {
        "client": "discord",
        "userid": Discord user ID
        "message": message
    }
    """
    global userid, client
    try:
        content = request.json
        client_id = content["client"]
        userid = content["userid"]
        user_message = content["message"]

        llm_response, status = reply_core(client_id, userid, user_message)

        return llm_response, status

    except Exception as e:
        app.logger.error("Error on reply: %s - Rolling back DB changes", e)
        db.session.rollback()

        user = get_user(userid, client)
        log_action(
            LogAction.DB_ROLLBACK,
            user=user if user else None,
            value={"error": str(e)},
            http_status=500,
            step="exception_handled"
        )

        with open("config/translations.json", "r", encoding="utf-8") as file:
            translations = json.load(file)

        if user:
            user_lang = get_language_by_id(user.language_id)
            return translations["translations"][user_lang.lang_code]["reply_error"], 200
        else:
            return translations["translations"]["en"]["create_error"], 500


# ---------------------------------------------------------------------------
# Survey endpoints
# ---------------------------------------------------------------------------

@app.route("/survey/<survey_id>", methods=["GET"])
@cross_origin()
def get_survey(survey_id):
    """Return the survey definition JSON for the given survey_id."""
    safe_name = os.path.basename(survey_id)  # prevent path traversal
    path = os.path.join(_CONFIG_DIR, f"survey_{safe_name}.json")
    if not os.path.isfile(path):
        return jsonify({"error": "Survey not found"}), 404
    with open(path, "r", encoding="utf-8") as f:
        survey = json.load(f)
    return jsonify(survey), 200


@app.route("/survey/<survey_id>/submit", methods=["POST", "OPTIONS"])
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


@app.route("/survey/<survey_id>/results", methods=["GET"])
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


# ---------------------------------------------------------------------------
# Researcher Dashboard endpoint
# ---------------------------------------------------------------------------

@app.route("/dashboard/stats", methods=["GET"])
@cross_origin()
def get_dashboard_stats():
    """Return aggregated statistics for the researcher dashboard."""
    try:
        from .models import (
            User, ConversationState, UserStrategy, StrategyTranslation,
            InterviewAnswer, LlmResponse, SurveyResponse, ActivityLog
        )
        import sqlalchemy as sa

        # 1. Total unique students
        total_students = db.session.query(
            sa.func.count(sa.distinct(User.id))
        ).scalar() or 0

        # 2. Completed interviews
        total_completed = db.session.query(
            sa.func.count(ConversationState.id)
        ).filter(ConversationState.interview_completed == True).scalar() or 0

        # 3. Avg interview duration + variance + std deviation
        duration_result = db.session.execute(sa.text("""
            SELECT
                AVG(EXTRACT(epoch FROM last_time) - EXTRACT(epoch FROM first_time)) as avg_dur,
                VARIANCE(EXTRACT(epoch FROM last_time) - EXTRACT(epoch FROM first_time)) as var_dur,
                STDDEV(EXTRACT(epoch FROM last_time) - EXTRACT(epoch FROM first_time)) as std_dur
            FROM (
                SELECT user_id, MIN(message_time) as first_time, MAX(message_time) as last_time
                FROM interview_answer
                GROUP BY user_id
            ) t
        """)).fetchone()
        avg_duration_minutes = round(float(duration_result[0]) / 60, 1) if duration_result[0] else 0
        var_duration_minutes = round(float(duration_result[1]) / 3600, 1) if duration_result[1] else 0
        std_duration_minutes = round(float(duration_result[2]) / 60, 1) if duration_result[2] else 0

        # 4. Avg LLM response time
        try:
            result = db.session.execute(sa.text("""
                SELECT AVG(r.timestamp - s.timestamp)
                FROM activity_log r
                JOIN activity_log s ON r.user_id = s.user_id
                WHERE r.action = 'reply_llm'
                AND s.action = 'api_call_start'
            """)).scalar()
            avg_response_time = round(float(result), 1) if result else 0
        except Exception:
            db.session.rollback()
            avg_response_time = 0

        # 5. Survey responses count
        try:
            survey_count = db.session.query(
                sa.func.count(SurveyResponse.id)
            ).scalar() or 0
        except Exception:
            db.session.rollback()
            survey_count = 0

        # 6. Drop-off analysis - at which step students left
        dropoff_rows = db.session.query(
            ConversationState.current_conversation_step,
            sa.func.count(ConversationState.id).label("count")
        ).filter(
            ConversationState.interview_completed == False
        ).group_by(
            ConversationState.current_conversation_step
        ).all()
        dropoff_distribution = [
            {"step": row.current_conversation_step or "not_started", "count": row.count}
            for row in dropoff_rows
        ]

        # 7. Strategy distribution
        strategy_rows = db.session.query(
            UserStrategy.strategy,
            sa.func.count(UserStrategy.strategy).label("count")
        ).group_by(UserStrategy.strategy).order_by(
            sa.func.count(UserStrategy.strategy).desc()
        ).all()
        strategy_distribution = [
            {"strategy": row.strategy, "count": row.count}
            for row in strategy_rows
        ]

        # 8. Re-attempts - students with more than one session
        reattempt_rows = db.session.execute(sa.text("""
            SELECT COUNT(*) as reattempts
            FROM (
                SELECT user_id, COUNT(*) as session_count
                FROM state
                GROUP BY user_id
                HAVING COUNT(*) > 1
            ) t
        """)).scalar() or 0

        # 9. Avg turns per completed vs incomplete interview
        avg_turns_completed = db.session.query(
            sa.func.avg(ConversationState.current_turn)
        ).filter(ConversationState.interview_completed == True).scalar()
        avg_turns_completed = round(float(avg_turns_completed), 1) if avg_turns_completed else 0

        avg_turns_incomplete = db.session.query(
            sa.func.avg(ConversationState.current_turn)
        ).filter(ConversationState.interview_completed == False).scalar()
        avg_turns_incomplete = round(float(avg_turns_incomplete), 1) if avg_turns_incomplete else 0

        # 10. Language distribution
        from .models import Language
        lang_rows = db.session.query(
            Language.lang_code,
            sa.func.count(User.id).label("count")
        ).join(Language, User.language_id == Language.id
               ).group_by(Language.lang_code).all()
        language_distribution = [
            {"language": row.lang_code, "count": row.count}
            for row in lang_rows
        ]

        # 11. Avg messages per interview
        avg_messages = db.session.execute(sa.text("""
                    SELECT AVG(msg_count) FROM (
                        SELECT user_id, COUNT(*) as msg_count
                        FROM interview_answer
                        GROUP BY user_id
                    ) t
                """)).scalar()
        avg_messages = round(float(avg_messages), 1) if avg_messages else 0

        return jsonify({
            "total_students": total_students,
            "total_completed": total_completed,
            "avg_duration_minutes": avg_duration_minutes,
            "var_duration_minutes": var_duration_minutes,
            "std_duration_minutes": std_duration_minutes,
            "avg_response_time_seconds": avg_response_time,
            "survey_count": survey_count,
            "reattempts": int(reattempt_rows),
            "avg_turns_completed": avg_turns_completed,
            "avg_turns_incomplete": avg_turns_incomplete,
            "dropoff_distribution": dropoff_distribution,
            "strategy_distribution": strategy_distribution,
            "language_distribution": language_distribution,
            "avg_messages_per_interview": avg_messages,
        }), 200

    except Exception as e:
        app.logger.error("Error fetching dashboard stats: %s", e)
        return jsonify({"error": str(e)}), 500
