from app import app, db
from app.models import Language, Context, Strategy, StrategyTranslation, StrategyVector
import json
import uuid
import os
import pandas as pd
import requests
from sqlalchemy import select, text
from app.db_utils.crud import get_language

app.app_context().push()

EMBEDDING_URL = os.getenv("EMBEDDING_URL", "https://api-inference.huggingface.co/pipeline/feature-extraction/")
EMBEDDING_TOKEN = os.getenv("EMBEDDING_TOKEN", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def embed_strategy_data(lang_code, lang_id):
    print("Reading strategy file for language", lang_code)
    try:
        df = pd.read_csv(f"app/config/strategies_test_{lang_code}.csv")
        df.head()

        for i in range(len(df.index)):
            print("Embedding example:", df['example'][i])
            strategy_example = df['example'][i]
            embedding = query_embeddings(strategy_example)
            vector_emb = StrategyVector(strategy=df['strategy'][i], description=df['example'][i], embedding=embedding,
                                        language_id=lang_id)
            db.session.add(vector_emb)
            db.session.commit()
    except FileNotFoundError:
        print("ERROR: Strategies file not found for language", lang_code)


def query_embeddings(text_to_embed):
    api_url = f"{EMBEDDING_URL}{EMBEDDING_MODEL}"
    headers = {"Authorization": f"Bearer {EMBEDDING_TOKEN}"}
    response = requests.post(api_url, headers=headers,
                             json={"inputs": text_to_embed, "options": {"wait_for_model": True}})
    return response.json()


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

            if lang_code == "en":
                for strategy in interview_context[lang_code]["strategies"]:
                    strategy_db = Strategy(id=strategy["id"])
                    db.session.add(strategy_db)
                    db.session.commit()

            for context in interview_context[lang_code]["contexts"]:
                context_db = Context(context=context, language_id=language_db.id)
                db.session.add(context_db)
                db.session.commit()

            for strategy in interview_context[lang_code]["strategies"]:
                translation_id = str(uuid.uuid4())
                strategy_db = StrategyTranslation(id=translation_id, strategy=strategy["id"], name=strategy["name"],
                                                  description=strategy["description"], language_id=language_db.id)
                db.session.add(strategy_db)
                db.session.commit()

        vectors_exist = db.session.execute(
            select(StrategyVector).where(StrategyVector.language_id == language_db.id)
        ).fetchone()
        if not vectors_exist:
            print("Creating vector embeddings for strategies")
            embed_strategy_data(lang_code, language_db.id)
        else:
            print("Vector embeddings data for strategies exists; skip embedding step")


if __name__ == "__main__":
    populate_contexts()
