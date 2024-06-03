import sqlite3
from flask import Flask, g, request
import json
from xml.sax.saxutils import escape as xmlescape
from html import escape as htmlescape

from llm import get_llm_message

DATABASE = 'database.db'

app = Flask(__name__)


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def db_insert_or_update(query, args=(), one=False):
    conn = get_db()
    cur = conn.cursor().execute(query, args)
    conn.commit()
    id = cur.lastrowid
    cur.close()
    if not id:
        count = cur.rowcount
        return count
    return id


def add_user(user_id, client, language, start_prompt):
    language_id = query_db("SELECT language_id FROM languages where lang_code = ?", [language], one=True)
    res = db_insert_or_update("INSERT INTO users VALUES (?, ?, ?, ?)", [user_id, client, language_id[0], start_prompt])
    if res:
        return True
    else:
        return False


@app.route("/status")
def hello_world():
    return "<p>Healthy</p>"


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
    with open("backend/translations.json") as file:
        translations = json.load(file)
    content = request.json
    language = content["language"]
    client = content["client"]
    userid = content["userid"]

    if language != "en" and language != "de":
        msg = translations["language_not_supported_message"]
        response = xmlescape(msg, {"ä": "&auml;", "ö": "&ouml;", "ü": "&uuml;"})
        return htmlescape(response), 400

    start_prompt = translations["translations"][language]["start_prompt"]["text"]
    llm_message = get_llm_message("mixtral", start_prompt)

    db_response = add_user(userid, client, language, f"<s>[INST]{start_prompt}[/INST]{llm_message}</s>")
    if db_response is not True:
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

    message_history = retrieve_user_context(userid, client)
    prompt = f"{message_history}[INST]{user_message}[/INST]"
    print(prompt)
    llm_message = get_llm_message("mixtral", prompt)
    res = db_insert_or_update(
        "UPDATE users SET message_history = message_history || ? WHERE user_id = ? and client = ?",
        [f"[INST]{user_message}[/INST]{llm_message}", userid, client])
    if res:
        return llm_message
    else:
        return "An error occurred, please try resending the message", 500


def retrieve_user_context(userid, client):
    message_history = query_db("SELECT message_history FROM users where user_id = ? and client = ?", [userid, client],
                               one=True)
    return message_history[0]
