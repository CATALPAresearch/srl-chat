from app import app, db
from app.models import User, Language

from flask import request
import json
import sqlalchemy as sa
from xml.sax.saxutils import escape as xmlescape
from html import escape as htmlescape

from app.llm import get_llm_message


@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"


@app.route('/user/<id>')
def get_user(id):
    user = db.session.scalar(
        sa.select(User).where(User.id == id))
    if user is None:
        return "User not found", 404
    return user.client


@app.route("/startConversation", methods=['POST'])
def start_conversation():
    """
    Post request format:
    {
        "language": "en" or "de",
        "client": "discord",
        "userid": Discord user ID
    }
    """
    with open("config/translations.json") as file:
        translations = json.load(file)
    with open("config/interview.json") as file:
        interview_context = json.load(file)
    content = request.json
    language = content["language"]
    client = content["client"]
    userid = content["userid"]

    if language != "en" and language != "de":
        msg = translations["language_not_supported_message"]
        response = xmlescape(msg, {"ä": "&auml;", "ö": "&ouml;", "ü": "&uuml;"})
        return htmlescape(response), 400

    # start_prompt = translations["translations"][language]["start_prompt"]["text"]
    start_prompt = get_start_prompt(interview_context[language]["contexts"][0])

    llm_message = get_llm_message("mixtral", start_prompt)

    language_db = db.session.scalar(
        sa.select(Language).where(Language.lang_code == language))
    user = User(id=userid, client=client, language_id=language_db.id,
                message_history=f"<s>[INST]{start_prompt}[/INST]{llm_message}</s>")
    db.session.add(user)
    db.session.commit()
    created_user = db.session.scalar(
        sa.select(User).where(User.id == userid and User.client == client))
    if created_user is None:
        return "An error occurred, please try to restart the conversation", 500
    # TODO: check if user has already started a conversation so we continue from there
    return llm_message


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
    # TODO error if conversation not started - redirect?
    content = request.json
    client = content["client"]
    userid = content["userid"]
    user_message = content["message"]

    with open("config/interview.json") as file:
        interview_context = json.load(file)
    strategies = interview_context["de"]["strategies"]
    eval_prompt = f"Evaluiere die Antwort der Nutzerin/des Nutzers, die durch '###' abgegrenzt ist. Bestimme, " \
                  f"ob die Antwort eine der folgenden Lernstrategien erwähnt und gib ihren Index in der folgenden " \
                  f"Liste an: {strategies} ### {user_message}"

    user = db.session.scalar(
        sa.select(User).where(User.id == userid and User.client == client))
    message_history = user.message_history
    # prompt = f"{message_history}[INST]{user_message}[/INST]"
    # llm_message = get_llm_message("mixtral", prompt)

    llm_message = get_llm_message("mixtral", eval_prompt)

    user.message_history += f"[INST]{user_message}[/INST]{llm_message}"
    db.session.commit()
    return llm_message


def get_start_prompt(context):
    return f"Du bist ein Studienberater an einer deutschen Universität. Deine Aufgabe ist es, die bevorzugten Lernmethoden von Studenten und Studentinnen zu evaluieren. Beginne das Gespräch mit einer freundlichen Begrüßung und einer Aufforderung, eine Lernmethode zu beschreiben, die die Person im Lernkontext '{context}' oft einsetzt. Antworte stets auf Deutsch und duze deinen Gesprächspartner. Sende und erwähne keine englische Übersetzung."