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
    """Return aggregated statistics for the researcher dashboard.
    Optional query params: date_from, date_to (Unix timestamps)
    """
    try:
        from .models import (
            User, ConversationState, UserStrategy,
            InterviewAnswer, LlmResponse, SurveyResponse, ActivityLog, Language
        )
        import sqlalchemy as sa

        # Date range filter
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")

        # Build date filter for interview_answer
        ia_date_filter = ""
        if date_from:
            ia_date_filter += f" AND message_time >= to_timestamp({int(date_from)})"
        if date_to:
            ia_date_filter += f" AND message_time <= to_timestamp({int(date_to)})"

        # Build user filter based on date
        user_id_filter = ""
        if date_from or date_to:
            date_users = db.session.execute(sa.text(f"""
                SELECT DISTINCT user_id FROM interview_answer WHERE 1=1 {ia_date_filter}
            """)).fetchall()
            user_ids = [r[0] for r in date_users]
            if user_ids:
                ids_str = "','".join(user_ids)
                user_id_filter = f" AND id IN ('{ids_str}')"
            else:
                # No users in range - return zeros
                return jsonify({
                    "total_students": 0, "total_completed": 0,
                    "avg_duration_minutes": 0, "var_duration_minutes": 0,
                    "std_duration_minutes": 0, "avg_response_time_seconds": 0,
                    "survey_count": 0, "reattempts": 0,
                    "avg_turns_completed": 0, "avg_turns_incomplete": 0,
                    "dropoff_distribution": [], "strategy_distribution": [],
                    "language_distribution": [], "avg_messages_per_interview": 0,
                    "completion_funnel": [], "weekly_activity": [],
                    "response_time_by_step": [], "total_messages": 0,
                    "survey_avg_scores": [],
                }), 200

        # 1. Total unique students
        total_students = db.session.execute(sa.text(f"""
            SELECT COUNT(DISTINCT id) FROM users WHERE 1=1 {user_id_filter}
        """)).scalar() or 0

        # 2. Completed interviews
        total_completed = db.session.execute(sa.text(f"""
            SELECT COUNT(*) FROM state
            WHERE interview_completed = true
            {'AND user_id IN (SELECT DISTINCT user_id FROM interview_answer WHERE 1=1 ' + ia_date_filter + ')' if ia_date_filter else ''}
        """)).scalar() or 0

        # 3. Avg interview duration + variance + std deviation
        duration_result = db.session.execute(sa.text(f"""
            SELECT
                AVG(EXTRACT(epoch FROM last_time) - EXTRACT(epoch FROM first_time)),
                VARIANCE(EXTRACT(epoch FROM last_time) - EXTRACT(epoch FROM first_time)),
                STDDEV(EXTRACT(epoch FROM last_time) - EXTRACT(epoch FROM first_time))
            FROM (
                SELECT user_id,
                    MIN(message_time) as first_time,
                    MAX(message_time) as last_time
                FROM interview_answer
                WHERE 1=1 {ia_date_filter}
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
                WHERE r.action = 'reply_llm' AND s.action = 'api_call_start'
            """)).scalar()
            avg_response_time = round(float(result), 1) if result else 0
        except Exception:
            db.session.rollback()
            avg_response_time = 0

        # 5. Survey responses count + avg scores
        try:
            survey_count = db.session.query(
                sa.func.count(SurveyResponse.id)
            ).scalar() or 0
            survey_rows = db.session.query(SurveyResponse).all()
            survey_avg_scores = {}
            for row in survey_rows:
                if row.responses:
                    for key, val in row.responses.items():
                        if isinstance(val, (int, float)):
                            if key not in survey_avg_scores:
                                survey_avg_scores[key] = []
                            survey_avg_scores[key].append(val)
            survey_avg_scores = [
                {"question": k, "avg": round(sum(v) / len(v), 2)}
                for k, v in survey_avg_scores.items()
            ]
        except Exception:
            db.session.rollback()
            survey_count = 0
            survey_avg_scores = []

        # 6. Drop-off analysis
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

        # 8. Re-attempts
        reattempt_rows = db.session.execute(sa.text("""
            SELECT COUNT(*) FROM (
                SELECT user_id, COUNT(*) as session_count
                FROM state GROUP BY user_id HAVING COUNT(*) > 1
            ) t
        """)).scalar() or 0

        # 9. Avg turns completed vs incomplete
        avg_turns_completed = db.session.query(
            sa.func.avg(ConversationState.current_turn)
        ).filter(ConversationState.interview_completed == True).scalar()
        avg_turns_completed = round(float(avg_turns_completed), 1) if avg_turns_completed else 0

        avg_turns_incomplete = db.session.query(
            sa.func.avg(ConversationState.current_turn)
        ).filter(ConversationState.interview_completed == False).scalar()
        avg_turns_incomplete = round(float(avg_turns_incomplete), 1) if avg_turns_incomplete else 0

        # 10. Language distribution
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
        avg_messages = db.session.execute(sa.text(f"""
            SELECT AVG(msg_count) FROM (
                SELECT user_id, COUNT(*) as msg_count
                FROM interview_answer WHERE 1=1 {ia_date_filter}
                GROUP BY user_id
            ) t
        """)).scalar()
        avg_messages = round(float(avg_messages), 1) if avg_messages else 0

        # 12. Total messages sent
        total_messages = db.session.execute(sa.text(f"""
            SELECT COUNT(*) FROM interview_answer WHERE 1=1 {ia_date_filter}
        """)).scalar() or 0

        # 13. Completion funnel
        funnel_steps = ['intro', 'strategy', 'frequency', 'complete']
        funnel = []
        for step in funnel_steps:
            count = db.session.execute(sa.text(f"""
                SELECT COUNT(DISTINCT user_id) FROM interview_answer
                WHERE conversation_step = '{step}' {ia_date_filter}
            """)).scalar() or 0
            funnel.append({"step": step, "count": count})

        # 14. Weekly activity
        weekly_activity = db.session.execute(sa.text(f"""
            SELECT
                DATE_TRUNC('week', message_time) as week,
                COUNT(*) as messages,
                COUNT(DISTINCT user_id) as users
            FROM interview_answer
            WHERE 1=1 {ia_date_filter}
            GROUP BY DATE_TRUNC('week', message_time)
            ORDER BY week
        """)).fetchall()
        weekly_activity = [
            {
                "week": str(row[0])[:10] if row[0] else "",
                "messages": row[1],
                "users": row[2]
            }
            for row in weekly_activity
        ]

        # 15. Avg response time by step
        try:
            step_response = db.session.execute(sa.text("""
                SELECT step, AVG(r.timestamp - s.timestamp) as avg_time
                FROM activity_log r
                JOIN activity_log s ON r.user_id = s.user_id
                WHERE r.action = 'reply_llm' AND s.action = 'api_call_start'
                GROUP BY step
            """)).fetchall()
            response_time_by_step = [
                {"step": row[0], "avg_seconds": round(float(row[1]), 1) if row[1] else 0}
                for row in step_response
            ]
        except Exception:
            db.session.rollback()
            response_time_by_step = []

        return jsonify({
            "total_students": total_students,
            "total_completed": total_completed,
            "avg_duration_minutes": avg_duration_minutes,
            "var_duration_minutes": var_duration_minutes,
            "std_duration_minutes": std_duration_minutes,
            "avg_response_time_seconds": avg_response_time,
            "survey_count": survey_count,
            "survey_avg_scores": survey_avg_scores,
            "reattempts": int(reattempt_rows),
            "avg_turns_completed": avg_turns_completed,
            "avg_turns_incomplete": avg_turns_incomplete,
            "dropoff_distribution": dropoff_distribution,
            "strategy_distribution": strategy_distribution,
            "language_distribution": language_distribution,
            "avg_messages_per_interview": avg_messages,
            "total_messages": total_messages,
            "completion_funnel": funnel,
            "weekly_activity": weekly_activity,
            "response_time_by_step": response_time_by_step,
        }), 200

    except Exception as e:
        app.logger.error("Error fetching dashboard stats: %s", e)
        return jsonify({"error": str(e)}), 500