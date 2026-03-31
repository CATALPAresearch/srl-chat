from flask import request, jsonify, send_from_directory
from flask_cors import CORS, cross_origin
import json
import os
import uuid
import glob

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
# Interview Protocol CRUD
# ---------------------------------------------------------------------------
@app.route("/protocols", methods=["GET"])
@cross_origin()
def list_protocols():
    """List all available interview protocols."""
    try:
        protocol_files = glob.glob(os.path.join(_CONFIG_DIR, "interview", "*.json"))
        protocols = []
        for f in protocol_files:
            name = os.path.splitext(os.path.basename(f))[0]
            protocols.append({"name": name, "filename": os.path.basename(f)})
        return jsonify(protocols), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/protocols/<name>", methods=["GET"])
@cross_origin()
def get_protocol(name):
    """Get a specific interview protocol by name."""
    try:
        safe_name = os.path.basename(name)
        path = os.path.join(_CONFIG_DIR, "interview", f"{safe_name}.json")
        if not os.path.isfile(path):
            return jsonify({"error": "Protocol not found"}), 404
        with open(path, "r", encoding="utf-8") as f:
            protocol = json.load(f)
        return jsonify(protocol), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/protocols", methods=["POST"])
@cross_origin()
def create_protocol():
    """Create a new interview protocol."""
    try:
        content = request.json
        name = content.get("name")
        protocol = content.get("protocol")
        if not name or not protocol:
            return jsonify({"error": "Missing name or protocol data"}), 400
        safe_name = os.path.basename(name).replace(" ", "_")
        path = os.path.join(_CONFIG_DIR, "interview", f"{safe_name}.json")
        if os.path.isfile(path):
            return jsonify({"error": "Protocol already exists"}), 409
        with open(path, "w", encoding="utf-8") as f:
            json.dump(protocol, f, indent=2, ensure_ascii=False)
        return jsonify({"status": "created", "name": safe_name}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/protocols/<name>", methods=["PUT"])
@cross_origin()
def update_protocol(name):
    """Update an existing interview protocol."""
    try:
        safe_name = os.path.basename(name)
        path = os.path.join(_CONFIG_DIR, "interview", f"{safe_name}.json")
        if not os.path.isfile(path):
            return jsonify({"error": "Protocol not found"}), 404
        protocol = request.json
        with open(path, "w", encoding="utf-8") as f:
            json.dump(protocol, f, indent=2, ensure_ascii=False)
        return jsonify({"status": "updated", "name": safe_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/protocols/<name>", methods=["DELETE"])
@cross_origin()
def delete_protocol(name):
    """Delete an interview protocol."""
    try:
        safe_name = os.path.basename(name)
        if safe_name == "interview_default":
            return jsonify({"error": "Cannot delete the default protocol"}), 403
        path = os.path.join(_CONFIG_DIR, "interview", f"{safe_name}.json")
        if not os.path.isfile(path):
            return jsonify({"error": "Protocol not found"}), 404
        os.remove(path)
        return jsonify({"status": "deleted", "name": safe_name}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/protocols/<name>/export", methods=["GET"])
@cross_origin()
def export_protocol(name):
    """Export a protocol as a downloadable JSON file."""
    try:
        safe_name = os.path.basename(name)
        path = os.path.join(_CONFIG_DIR, "interview", f"{safe_name}.json")
        if not os.path.isfile(path):
            return jsonify({"error": "Protocol not found"}), 404
        return send_from_directory(
            os.path.join(_CONFIG_DIR, "interview"),
            f"{safe_name}.json",
            as_attachment=True,
            download_name=f"{safe_name}.json"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/protocols/import", methods=["POST"])
@cross_origin()
def import_protocol():
    """Import a protocol from uploaded JSON."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        name = os.path.splitext(file.filename)[0]
        safe_name = os.path.basename(name).replace(" ", "_")
        protocol = json.load(file)
        path = os.path.join(_CONFIG_DIR, "interview", f"{safe_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(protocol, f, indent=2, ensure_ascii=False)
        return jsonify({"status": "imported", "name": safe_name}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500