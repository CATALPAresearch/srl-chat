from app import app, db
from app.models import User, Language, LlmResponse, ConversationState, Strategy, Context, InterviewAnswer, ConversationCompletedContexts
import sqlalchemy as sa
import json
import uuid

with open("config/translations.json") as file:
    translations = json.load(file)
with open("config/interview.json") as file:
    interview_context = json.load(file)


def get_user(userid, client) -> User | None:
    user = db.session.scalar(
        sa.select(User).where(User.id == userid).where(User.client == client)
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
    result = [con for con, in contexts]
    return result


def get_context_by_id(context_id):
    context = db.session.scalar(
        sa.select(Context).where(Context.id == context_id))
    return context


def get_strategy_by_id(strategy_id):
    strategy = db.session.scalar(
        sa.select(Strategy).where(Strategy.id == strategy_id))
    return strategy


def set_context_completed(user, context):
    completed_contexts = ConversationCompletedContexts(
        conversation_id=user.conversation_state.id,
        completed_context_id=context
    )
    db.session.add(completed_contexts)
    db.session.commit()


def get_completed_contexts(user):
    completed_contexts = db.session.execute(
        sa.select(ConversationCompletedContexts)
        .where(ConversationCompletedContexts.conversation_id == user.conversation_state.id)
    ).all()
    completed_contexts_result = [con.completed_context_id for con, in completed_contexts]
    contexts = db.session.execute(
        sa.select(Context)
        .where(Context.id.in_(completed_contexts_result))
    ).all()
    result = [con for con, in contexts]
    return result


def get_strategies(lang_id):
    strats = db.session.execute(
        sa.select(Strategy.id, Strategy.strategy, Strategy.description)
        .where(Strategy.language_id == lang_id)
    ).all()
    return strats


def get_answers_for_context(user, context_id):
    answers = db.session.scalars(
        sa.select(InterviewAnswer)
        .where(InterviewAnswer.user == user)
        .where(InterviewAnswer.context == context_id)
    ).all()
    return answers


def first_time_setup(userid, client, language):
    language_db = get_language(language)
    user = User(id=userid, client=client, language_id=language_db.id,
                message_history="",
                conversation_state=ConversationState(id=str(uuid.uuid4())))
    db.session.add(user)
    db.session.commit()
    created_user = db.session.scalar(
        sa.select(User)
        .where(User.id == userid)
        .where(User.client == client))
    return created_user


def set_current_context(user, context):
    user.conversation_state.current_context = context.id
    db.session.commit()


def update_most_recent_response(user, response):
    user.conversation_state.most_recent_response = response
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


def store_llm_answer(user, message):
    answer_id = str(uuid.uuid4())
    answer = LlmResponse(id=answer_id,
                         user=user,
                         message=message)
    db.session.add(answer)
    db.session.commit()
    created_answer = db.session.scalar(
        sa.select(LlmResponse).where(LlmResponse.id == answer_id)
    )
    return created_answer


def update_answer_with_frequency(user, context_id, strategy_id, frequency):
    answer = db.session.scalar(
        sa.select(InterviewAnswer)
        .where(InterviewAnswer.user == user)
        .where(InterviewAnswer.context == context_id)
        .where(InterviewAnswer.strategy == strategy_id)
    )
    answer.frequency = frequency
    db.session.commit()
