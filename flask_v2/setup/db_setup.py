from app import app, db
from app.models import Language, Context, Strategy
import json
import uuid
from db_utils.crud import get_language

app.app_context().push()


def populate_contexts():
    print("Populating contexts and strategies into DB")
    with open("config/interview.json") as file:
        interview_context = json.load(file)
    for lang_code in interview_context:
        print(lang_code)
        lang_id = str(uuid.uuid4())
        lang = Language(id=lang_id, lang_code=lang_code)
        db.session.add(lang)
        db.session.commit()
        language_db = get_language(lang_code)
        for context in interview_context[lang_code]["contexts"]:
            context_db = Context(context=context, language_id=language_db.id)
            db.session.add(context_db)
            db.session.commit()
        for strategy in interview_context[lang_code]["strategies"]:
            strategy_db = Strategy(strategy=strategy["name"], description=strategy["description"], language_id=language_db.id)
            db.session.add(strategy_db)
            db.session.commit()
