from app import app, db
from app.models import User, Language

from flask import request
import json
import sqlalchemy as sa
from xml.sax.saxutils import escape as xmlescape
from html import escape as htmlescape

from app.llm import get_llm_message
from controller.conversation_controller import get_language, get_language_by_id, get_user, first_time_setup, get_strategies, get_contexts


@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"


@app.route('/user/<id>')
def get_user_by_id(id):
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

    if not get_language(language):
        msg = translations["language_not_supported_message"]
        response = xmlescape(msg, {"ä": "&auml;", "ö": "&ouml;", "ü": "&uuml;"})
        return htmlescape(response), 400

    created_user = first_time_setup(userid, client, language)
    if created_user is None:
        return "An error occurred, please try to restart the conversation", 500

    # start_prompt = translations["translations"][language]["start_prompt"]["text"]
    start_prompt = get_start_prompt(interview_context[language]["contexts"][0])

    llm_message = get_llm_message("mixtral", start_prompt, 0.8)

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
    content = request.json
    client = content["client"]
    userid = content["userid"]
    user_message = content["message"]

    user = get_user(userid, client)
    if user is None:
        language = "en" # TODO - always supply or ask first time?
        return start_conversation(language, client, userid)

    if user.conversation_state.interview_completed:
        pass

    if user.conversation_state.last_answered_context == 0:
        pass
        # start_interview(user)

    strategies = get_strategies(user.language_id)
    prompt = get_eval_prompt(strategies, user_message, user)

    llm_message = get_llm_message("mixtral", prompt, 1)

    user.message_history += f"[INST]{user_message}[/INST]{llm_message}"
    db.session.commit()
    return llm_message


def get_start_prompt(context, user):
    with open("config/prompts.json") as file:
        prompts = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    prompt = prompts[user_lang.lang_code]["start"].replace("${context}", str(context))
    return prompt


def get_eval_prompt(strategies, user_message, user):
    with open("config/prompts.json") as file:
        prompts = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    prompt = prompts[user_lang.lang_code]["eval"].replace("${strategies}", str(strategies)).replace("${user_message}", user_message)
    return prompt


def start_conversation(language, client, userid):
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

    if not get_language(language):
        msg = translations["language_not_supported_message"]
        response = xmlescape(msg, {"ä": "&auml;", "ö": "&ouml;", "ü": "&uuml;"})
        return htmlescape(response), 400

    created_user = first_time_setup(userid, client, language)
    if created_user is None:
        return "An error occurred, please try to restart the conversation", 500

    start_prompt = get_start_prompt(interview_context[language]["contexts"][0])

    llm_message = get_llm_message("mixtral", start_prompt, 0.8)

    return llm_message


def start_interview(user: User):
    contexts = get_contexts(user.language_id)
