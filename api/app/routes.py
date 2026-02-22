from flask import request, jsonify
from flask_cors import CORS, cross_origin
import json

from app import app, db
from .core import start_conversation_core, reply_core, reset_conversation
from .db_utils.crud import get_user, get_language_by_id
from .actions import LogAction
from .logging_utlis import log_action

cors = CORS(app)
# FixMe: cors = CORS(app, ressources={r"/api/*": {"origin": "http://localhost:80"}})

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(error)
    db.session.rollback()
    with open("app/config/translations.json", "r", encoding="utf-8") as file:
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
    return "OK"


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
        with open("app/config/translations.json", "r", encoding="utf-8") as file:
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
    with open("app/config/translations.json", "r", encoding="utf-8") as file:
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
    with open("app/config/translations.json", "r", encoding="utf-8") as file:
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

        with open("app/config/translations.json", "r", encoding="utf-8") as file:
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
        client = content["client"]
        userid = content["userid"]
        user_message = content["message"]

        return reply_core(client, userid, user_message)

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

        with open("app/config/translations.json", "r", encoding="utf-8") as file:
            translations = json.load(file)

        if user:
            user_lang = get_language_by_id(user.language_id)
            return translations["translations"][user_lang.lang_code]["reply_error"], 200
        else:
            return translations["translations"]["en"]["create_error"], 500

