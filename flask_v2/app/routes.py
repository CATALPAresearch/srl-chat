from app import app

from flask import request, jsonify
import json

from .core import start_conversation_core, reply_core


@app.route('/')
def index():
    return "OK"


@app.route("/translations/<language>", methods=["GET"])
def get_translations(language):
    with open("config/translations.json", "r", encoding="utf-8") as file:
        translations = json.load(file)
    if language in list(translations["translations"].keys()):
        return translations["translations"][language]
    else:
        return jsonify(translations["language_not_supported_message"]), 400


@app.route("/startConversation", methods=['POST'])
def start_conversation_flask():
    """
    Post request format:
    {
        "language": "en" or "de",
        "client": "discord",
        "userid": Discord user ID
    }
    """
    content = request.json
    language = content["language"]
    client = content["client"]
    userid = content["userid"]

    return start_conversation_core(language, client, userid)


@app.route("/reply", methods=['POST'])
def reply():
    """
    Post request format:
    {
        "client": "discord",
        "userid": Discord user ID
        "message": message
    }
    """
    content = request.json
    client = content["client"]
    userid = content["userid"]
    user_message = content["message"]

    return reply_core(client, userid, user_message)