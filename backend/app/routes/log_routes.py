"""Telemetry logging routes: tab events and mouse traces."""
import sqlalchemy as sa
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

from app import app, db
from ..database.crud import get_user
from ..actions import LogAction
from ..logging_utlis import log_action

logs_bp = Blueprint('logs', __name__)


@logs_bp.route("/log/tab_event", methods=["POST", "OPTIONS"])
@cross_origin()
def log_tab_event():
    """
    Log when a user leaves or returns to the browser tab.
    Expected JSON body:
    {
        "userid": "...",
        "client": "...",
        "event": "tab_hidden" or "tab_visible",
        "timestamp": 1234567890
    }
    """
    try:
        content = request.json
        userid = content.get("userid")
        client = content.get("client")
        event = content.get("event")
        timestamp = content.get("timestamp")

        if event not in ["tab_hidden", "tab_visible"]:
            return jsonify({"error": "Invalid event type"}), 400

        action = LogAction.TAB_HIDDEN if event == "tab_hidden" else LogAction.TAB_VISIBLE
        user = get_user(userid, client)

        log_action(
            action,
            user=user,
            value={"event": event, "timestamp": timestamp, "userid": userid, "client": client},
            http_status=200,
            step="tab_event",
        )

        app.logger.info("Tab event: %s for user %s/%s", event, userid, client)
        return jsonify({"status": "logged", "event": event}), 200

    except Exception as e:
        app.logger.error("Error logging tab event: %s", e)
        return jsonify({"error": str(e)}), 500


@logs_bp.route("/log/mouse_traces", methods=["POST", "OPTIONS"])
@cross_origin()
def log_mouse_traces():
    """
    Store a batch of mouse position traces.
    Expected JSON body:
    {
        "userid": "...",
        "client": "...",
        "session_id": "...",
        "traces": [{"x": 100, "y": 200, "timestamp": 1234567890, ...}, ...]
    }
    """
    try:
        content = request.json
        userid = content.get("userid")
        client = content.get("client")
        session_id = content.get("session_id")
        traces = content.get("traces", [])

        if not userid or not client or not traces:
            return jsonify({"error": "Missing required fields"}), 400

        with db.engine.connect() as conn:
            for trace in traces:
                conn.execute(sa.text("""
                    INSERT INTO mouse_traces
                        (user_id, user_client, x, y, page_width, page_height, timestamp, session_id)
                    VALUES
                        (:user_id, :user_client, :x, :y, :page_width, :page_height, :timestamp, :session_id)
                """), {
                    "user_id": userid,
                    "user_client": client,
                    "x": trace.get("x", 0),
                    "y": trace.get("y", 0),
                    "page_width": trace.get("page_width"),
                    "page_height": trace.get("page_height"),
                    "timestamp": trace.get("timestamp"),
                    "session_id": session_id,
                })
            conn.commit()

        app.logger.info("Stored %d mouse traces for user %s/%s", len(traces), userid, client)
        return jsonify({"status": "stored", "count": len(traces)}), 200

    except Exception as e:
        app.logger.error("Error storing mouse traces: %s", e)
        return jsonify({"error": str(e)}), 500
