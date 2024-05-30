import json
import sqlite3
import uuid
from api import init_db, get_db

DATABASE = 'database.db'

init_db()

with open("backend/translations.json") as file:
    translations = json.load(file)
connection = sqlite3.connect(DATABASE)
cursor = connection.cursor()

languages = translations["translations"]
for lang in languages:
    print(lang)
    lang_query = cursor.execute("SELECT language_id FROM language where lang_code = ?", (lang,))
    lang_res = lang_query.fetchone()
    if not lang_res:
        lang_id = str(uuid.uuid4())
        print(lang_id)
        cursor.execute("INSERT INTO language VALUES (?, ?)",
                       (lang_id, lang))
        connection.commit()
    else:
        lang_id = lang_res[0]
        print(lang_id)
    start_prompt_version = languages[lang]["start_prompt"]["version"]
    prompt_query = cursor.execute("SELECT * FROM prompt where version = ? and language_id = ?", (str(start_prompt_version), lang_id))
    rows = prompt_query.fetchall()
    if not rows:
        cursor.execute("INSERT INTO prompt VALUES (?, ?, ?, ?)", (str(uuid.uuid4()), start_prompt_version, languages[lang]["start_prompt"]["text"], lang_id))
        connection.commit()
    else:
        print(rows)

connection.close()
