import json
import uuid
import os
import pandas as pd
from sqlalchemy import select, text

from app import app, db
from app.models import Language, Context, Strategy, StrategyTranslation, StrategyVector
from app.db_utils.crud import get_language
from app.llm import query_embeddings

app.app_context().push()

EMBEDDING_URL = os.getenv("EMBEDDING_URL", "https://api-inference.huggingface.co/pipeline/feature-extraction/")
EMBEDDING_TOKEN = os.getenv("EMBEDDING_TOKEN", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def embed_strategy_data(strategy, lang_id):
    embedding = query_embeddings(strategy["description"])
    vector_emb = StrategyVector(strategy=strategy["id"], description=strategy["description"],
                                embedding=embedding, language_id=lang_id)
    db.session.add(vector_emb)
    db.session.commit()


def populate_contexts():
    db.session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    db.session.commit()
    db.create_all()
    print("Populating contexts and strategies into DB")
    with open("app/config/interview.json", "r", encoding="utf-8") as file:
        interview_context = json.load(file)
    for lang_code in interview_context:
        if get_language(lang_code):
            print(f"Language {lang_code} already exists")
        else:
            print(lang_code)
            lang_id = str(uuid.uuid4())
            lang = Language(id=lang_id, lang_code=lang_code)
            db.session.add(lang)
            db.session.commit()
            language_db = get_language(lang_code)
            vectors_exist = db.session.execute(
                select(StrategyVector).where(StrategyVector.language_id == language_db.id)
            ).fetchone()

            if lang_code == "en":
                for category in interview_context[lang_code]["categories"]:
                    for strategy in interview_context[lang_code]["categories"][category]["strategies"]:
                        strategy_db = Strategy(id=strategy["id"])
                        db.session.add(strategy_db)
                        db.session.commit()

            for context in interview_context[lang_code]["contexts"]:
                context_db = Context(context=context, language_id=language_db.id)
                db.session.add(context_db)
                db.session.commit()

            for category in interview_context[lang_code]["categories"]:
                for strategy in interview_context[lang_code]["categories"][category]["strategies"]:
                    translation_id = str(uuid.uuid4())
                    strategy_db = StrategyTranslation(id=translation_id, strategy=strategy["id"], name=strategy["name"],
                                                      description=strategy["description"], language_id=language_db.id)
                    db.session.add(strategy_db)
                    db.session.commit()

                    if not vectors_exist:
                        print("Creating vector embeddings for strategies")
                        embed_strategy_data(strategy, language_db.id)


if __name__ == "__main__":
    populate_contexts()
