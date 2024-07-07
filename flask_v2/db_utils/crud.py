from app import app, db
from app.models import User, Language, ConversationState, Strategy, Context, InterviewAnswer
import sqlalchemy as sa
import json
import uuid

with open("config/translations.json") as file:
    translations = json.load(file)
with open("config/interview.json") as file:
    interview_context = json.load(file)


def get_user(userid, client) -> User | None:
    user = db.session.scalar(
        sa.select(User).where(User.id == userid and User.client == client)
        .join(User.conversation_state))
    return user


def get_language(lang_code) -> Language | None:
    language_db = db.session.scalar(
        sa.select(Language).where(Language.lang_code == lang_code))
    return language_db


def get_language_by_id(lang_id) -> Language | None:
    language_db = db.session.scalar(
        sa.select(Language).where(Language.id == lang_id))
    return language_db


def get_contexts(lang_id):
    contexts = db.session.execute(
        sa.select(Context)
        .where(Context.language_id == lang_id)
    ).all()
    return contexts


def get_strategies(lang_id):
    strats = db.session.execute(
        sa.select(Strategy.id, Strategy.strategy, Strategy.description)
        .where(Strategy.language_id == lang_id)
    ).all()
    return strats


def first_time_setup(userid, client, language):
    language_db = get_language(language)
    user = User(id=userid, client=client, language_id=language_db.id,
                message_history="",
                conversation_state=ConversationState(id=str(uuid.uuid4())))
    db.session.add(user)
    db.session.commit()
    created_user = db.session.scalar(
        sa.select(User).where(User.id == userid and User.client == client))
    return created_user


def set_current_context(user, context):
    user.conversation_state.current_context = context[0].id
    db.session.commit()


def store_answer(user, context, strategy, message):
    answer_id = str(uuid.uuid4())
    answer = InterviewAnswer(id=answer_id,
                             user=user,
                             context=context,
                             strategy=strategy,
                             message=message)
    db.session.add(answer)
    db.session.commit()
    created_answer = db.session.scalar(
        sa.select(InterviewAnswer).where(InterviewAnswer.id == answer_id)
    )
    return created_answer


def converse(userid, client):
    user = get_user(userid, client)
    if not user.conversation_state.interview_completed:
        print("nope")
