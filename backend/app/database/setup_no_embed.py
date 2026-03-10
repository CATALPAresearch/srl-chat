"""db_setup without the embedding step (which needs an external API)."""
import json
import uuid
from sqlalchemy import text

from app import app, db
from app.models import Language, Context, Strategy, StrategyTranslation
from app.database.crud import get_language

app.app_context().push()

db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
db.session.commit()
db.create_all()
print("Tables created.")

from app.config import get_interview_config_path
with open(get_interview_config_path(), "r", encoding="utf-8") as f:
    interview_context = json.load(f)

for lang_code in interview_context:
    if get_language(lang_code):
        print(f"Language {lang_code} already exists")
        continue
    print(f"Setting up language {lang_code}")
    lang_id = str(uuid.uuid4())
    lang = Language(id=lang_id, lang_code=lang_code)
    db.session.add(lang)
    db.session.commit()
    language_db = get_language(lang_code)

    if lang_code == "en":
        for category in interview_context[lang_code]["categories"]:
            for strategy in category["strategies"]:
                strategy_db = Strategy(id=strategy["id"])
                db.session.add(strategy_db)
                db.session.commit()

    for context in interview_context[lang_code]["contexts"]:
        context_db = Context(context=context, language_id=language_db.id)
        db.session.add(context_db)
        db.session.commit()

    for category in interview_context[lang_code]["categories"]:
        for strategy in category["strategies"]:
            translation_id = str(uuid.uuid4())
            strat_t = StrategyTranslation(
                id=translation_id,
                strategy=strategy["id"],
                name=strategy["name"],
                description=strategy["description"],
                language_id=language_db.id,
            )
            db.session.add(strat_t)
            db.session.commit()

print("DB setup complete (embeddings skipped).")
