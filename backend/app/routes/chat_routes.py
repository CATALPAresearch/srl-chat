"""Chat / conversation routes: start, reply, reset, history."""
import json

import sqlalchemy as sa
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

from app import app, db
from ..core import start_conversation_core, reply_core, reset_conversation
from ..database.crud import get_user, get_language_by_id
from ..actions import LogAction
from ..logging_utlis import log_action

chat_bp = Blueprint('chat', __name__)


@chat_bp.route("/resetConversation", methods=["POST", "OPTIONS"])
@cross_origin()
def delete_message():
    userid = None
    client = None
    try:
        content = request.json
        client = content["client"]
        userid = content["userid"]
        app.logger.info("Resetting conversation for user: %s - %s", userid, client)
        user = get_user(userid, client)
        success = reset_conversation(user)
        if success:
            return (
                "*** Conversation has been reset. "
                "A new conversation can be started from the StudyTest server. ***"
            ), 200
        return None
    except Exception as e:
        app.logger.error("Error on reset conversation: %s - Rolling back DB changes", e)
        db.session.rollback()
        with open("config/translations.json", "r", encoding="utf-8") as file:
            translations = json.load(file)
        user = get_user(userid, client) if userid and client else None
        if user:
            user_lang = get_language_by_id(user.language_id)
            return translations["translations"][user_lang.lang_code]["reply_error"], 200
        return translations["translations"]["en"]["create_error"], 500


@chat_bp.route("/startConversation", methods=['POST'])
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
    language = None
    try:
        content = request.json
        language = content["language"]
        client = content["client"]
        userid = content["userid"]
        app.logger.info(
            "Starting new conversation (%s) for user: %s - %s", language, userid, client
        )

        user = get_user(userid, client)
        log_action(
            LogAction.API_CALL_START,
            user=user,
            value={
                "endpoint": "/startConversation",
                "language": language,
                "client": client,
                "userid": userid,
            },
            http_status=200,
            turn=0,
            step="request_received",
            context="conversation_start",
            strategy="strategy_not_detected",
        )

        return start_conversation_core(language, client, userid)
    except Exception as e:
        app.logger.error("Error on start conversation: %s - Rolling back DB changes", e)
        db.session.rollback()
        log_action(
            LogAction.DB_ROLLBACK,
            value={"error": str(e)},
            http_status=500,
            step="exception_handled",
        )
        with open("config/translations.json", "r", encoding="utf-8") as file:
            translations = json.load(file)
        lang = language or "en"
        return translations["translations"].get(lang, translations["translations"]["en"])["create_error"], 500


@chat_bp.route("/reply", methods=['POST'])
@cross_origin()
def reply():
    """
    Post request format:
    {
        "client": "discord",
        "userid": Discord user ID,
        "message": message
    }
    """
    client_id = None
    userid = None
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

        user = get_user(userid, client_id) if userid and client_id else None
        log_action(
            LogAction.DB_ROLLBACK,
            user=user,
            value={"error": str(e)},
            http_status=500,
            step="exception_handled",
        )

        with open("config/translations.json", "r", encoding="utf-8") as file:
            translations = json.load(file)

        if user:
            user_lang = get_language_by_id(user.language_id)
            return translations["translations"][user_lang.lang_code]["reply_error"], 200
        return translations["translations"]["en"]["create_error"], 500


@chat_bp.route("/conversation", methods=["GET"])
@cross_origin()
def get_conversation():
    """Return the full conversation history for a user, ordered chronologically.

    Query params: userid, client
    Response: { "messages": [{"author": "user"|"bot", "message": "...", "id": <int>}, ...] }
    """
    userid = request.args.get("userid")
    client = request.args.get("client")
    if not userid or not client:
        return jsonify({"messages": []}), 400

    try:
        user_rows = db.session.execute(sa.text("""
            SELECT turn, message, message_time, 'user' AS author
            FROM interview_answer
            WHERE user_id = :uid AND user_client = :client
        """), {"uid": userid, "client": client}).fetchall()

        bot_rows = db.session.execute(sa.text("""
            SELECT turn, message, message_time, 'bot' AS author
            FROM llm_response
            WHERE user_id = :uid AND user_client = :client
        """), {"uid": userid, "client": client}).fetchall()

        all_rows = [
            {"turn": r[0], "message": r[1], "time": r[2], "author": r[3]}
            for r in (list(user_rows) + list(bot_rows))
        ]
        # Sort by timestamp; within same turn put user message before bot reply
        all_rows.sort(key=lambda r: (r["time"], 0 if r["author"] == "user" else 1))

        messages = [
            {"author": r["author"], "message": r["message"], "id": i + 1}
            for i, r in enumerate(all_rows)
        ]
        return jsonify({"messages": messages}), 200

    except Exception as e:
        app.logger.error("Error fetching conversation: %s", e)
        db.session.rollback()
        return jsonify({"messages": []}), 500
