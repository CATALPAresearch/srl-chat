"""Researcher dashboard routes."""
import sqlalchemy as sa
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

from app import app, db
from ..models import (
    User, ConversationState, UserStrategy, SurveyResponse, Language,
)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route("/dashboard/stats", methods=["GET"])
@cross_origin()
def get_dashboard_stats():
    """Return aggregated statistics for the researcher dashboard.
    Optional query params: date_from, date_to (Unix timestamps)
    """
    try:
        date_from = request.args.get("date_from")
        date_to = request.args.get("date_to")

        ia_date_filter = ""
        if date_from:
            ia_date_filter += f" AND message_time >= to_timestamp({int(date_from)})"
        if date_to:
            ia_date_filter += f" AND message_time <= to_timestamp({int(date_to)})"

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

        # 4. Avg LLM response time (REPLY_LLM.timestamp - REPLY_USER.timestamp, same turn)
        try:
            result = db.session.execute(sa.text("""
                SELECT AVG(llm.timestamp - usr.timestamp)
                FROM activity_log llm
                JOIN activity_log usr
                  ON llm.user_id = usr.user_id
                 AND llm.turn    = usr.turn
                WHERE llm.action = 'reply_llm'
                  AND usr.action = 'reply_user'
                  AND llm.timestamp > usr.timestamp
            """)).scalar()
            avg_response_time = round(float(result), 1) if result else 0
        except Exception:
            db.session.rollback()
            avg_response_time = 0

        # 5. Survey responses count + avg scores per question
        try:
            survey_count = db.session.query(sa.func.count(SurveyResponse.id)).scalar() or 0
            survey_avg_scores_map: dict[str, list] = {}
            for row in db.session.query(SurveyResponse).all():
                if row.responses:
                    for key, val in row.responses.items():
                        if isinstance(val, (int, float)):
                            survey_avg_scores_map.setdefault(key, []).append(val)
            survey_avg_scores = [
                {"question": k, "avg": round(sum(v) / len(v), 2)}
                for k, v in survey_avg_scores_map.items()
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
        ).group_by(ConversationState.current_conversation_step).all()
        dropoff_distribution = [
            {"step": row.current_conversation_step or "not_started", "count": row.count}
            for row in dropoff_rows
        ]

        # 7. Strategy distribution with English names
        strategy_rows = db.session.execute(sa.text("""
            SELECT us.strategy, COUNT(*) as count,
                COALESCE(
                    (SELECT st2.name FROM strategy_translation st2
                     JOIN languages l2 ON l2.id = st2.language_id
                     WHERE st2.strategy = us.strategy AND l2.lang_code = 'en'
                     LIMIT 1),
                    (SELECT st3.name FROM strategy_translation st3
                     JOIN languages l3 ON l3.id = st3.language_id
                     WHERE st3.strategy = us.strategy AND l3.lang_code = 'de'
                     LIMIT 1),
                    us.strategy
                ) as strategy_name
            FROM user_strategy us
            GROUP BY us.strategy
            ORDER BY count DESC
        """)).fetchall()
        strategy_distribution = [
            {"strategy": row[0], "name": row[2], "count": row[1]}
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
        ).join(Language, User.language_id == Language.id).group_by(Language.lang_code).all()
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
            {"week": str(row[0])[:10] if row[0] else "", "messages": row[1], "users": row[2]}
            for row in weekly_activity
        ]

        # 15. Avg response time by step (REPLY_LLM - REPLY_USER on same user+turn)
        try:
            step_response = db.session.execute(sa.text("""
                SELECT llm.step, AVG(llm.timestamp - usr.timestamp) as avg_time
                FROM activity_log llm
                JOIN activity_log usr
                  ON llm.user_id = usr.user_id
                 AND llm.turn    = usr.turn
                WHERE llm.action = 'reply_llm'
                  AND usr.action = 'reply_user'
                  AND llm.timestamp > usr.timestamp
                GROUP BY llm.step
            """)).fetchall()
            response_time_by_step = [
                {"step": row[0], "avg_seconds": round(float(row[1]), 1) if row[1] else 0}
                for row in step_response
            ]
        except Exception:
            db.session.rollback()
            response_time_by_step = []

        # 16. Last activity
        last_activity = db.session.execute(sa.text(f"""
            SELECT MAX(message_time) FROM interview_answer WHERE 1=1 {ia_date_filter}
        """)).scalar()
        last_activity_str = last_activity.strftime("%Y-%m-%d %H:%M") if last_activity else None

        # 17. Avg time between student responses (thinking time proxy)
        try:
            gap_result = db.session.execute(sa.text(f"""
                SELECT AVG(gap_seconds) FROM (
                    SELECT
                        EXTRACT(epoch FROM message_time - LAG(message_time)
                            OVER (PARTITION BY user_id ORDER BY message_time)) as gap_seconds
                    FROM interview_answer
                    WHERE 1=1 {ia_date_filter}
                ) t
                WHERE gap_seconds > 0 AND gap_seconds < 3600
            """)).scalar()
            avg_response_gap = round(float(gap_result), 1) if gap_result else 0
        except Exception:
            db.session.rollback()
            avg_response_gap = 0

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
            "last_activity": last_activity_str,
            "avg_response_gap_seconds": avg_response_gap,
        }), 200

    except Exception as e:
        app.logger.error("Error fetching dashboard stats: %s", e)
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/dashboard/courses", methods=["GET"])
@cross_origin()
def get_dashboard_courses():
    """Return list of distinct courses from LTI context data."""
    try:
        # TODO: Add context_id and context_title columns to users table during LTI launch.
        rows = db.session.execute(sa.text("""
            SELECT DISTINCT context_id, context_title, COUNT(*) as students
            FROM users
            WHERE context_id IS NOT NULL
            GROUP BY context_id, context_title
            ORDER BY students DESC
        """)).fetchall()
        return jsonify([
            {"id": r[0], "name": r[1] or r[0], "students": r[2]}
            for r in rows
        ]), 200
    except Exception as e:
        db.session.rollback()
        return jsonify([]), 200
