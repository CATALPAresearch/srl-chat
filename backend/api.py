import sqlite3
from flask import Flask, g
import json
from xml.sax.saxutils import escape as xmlescape
from html import escape as htmlescape


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


@app.route("/status")
def hello_world():
    return "<p>Healthy</p>"


@app.route("/startConversation/<string:language>/<int:userid>/<string:username>")
def start_conversation(language, userid, username):
    with open("backend/translations.json") as file:
        translations = json.load(file)
    if language != "en" and language != "de":
        msg = translations["language_not_supported_message"]
        response = xmlescape(msg, {"ä": "&auml;", "ö": "&ouml;", "ü": "&uuml;"})
        return htmlescape(response), 400
    return "Hey " + username

