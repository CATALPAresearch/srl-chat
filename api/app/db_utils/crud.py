import logging
import numpy as np
from app import app, db
from app.models import (
    Archive,
    User,
    Language,
    LlmResponse,
    ConversationState,
    Strategy,
    StrategyTranslation,
    StrategyVector,
    Context,
    InterviewAnswer,
    ConversationCompletedContexts,
    UserStrategy,
    StrategyEvaluation
)
import sqlalchemy as sa
import uuid

logger = logging.getLogger("StudyBot")


def get_user(userid, client) -> User | None:
    user = db.session.scalar(
        sa.select(User).where(User.id == str(userid)).where(User.client == client)
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


def get_contexts_content(lang_id):
    contexts = db.session.execute(
        sa.select(Context)
        .where(Context.language_id == lang_id)
    ).all()
    result = [con.context for con, in contexts]
    return result


def get_context_by_id(context_id):
    context = db.session.scalar(
        sa.select(Context).where(Context.id == context_id))
    return context


def get_all_strategies():
    strategies = db.session.execute(
        sa.select(Strategy)
    ).all()
    result = [strat.id for strat, in strategies]
    return result


def get_strategies_content(lang_id):
    strategies = db.session.execute(
        sa.select(StrategyTranslation)
        .where(StrategyTranslation.language_id == lang_id)
    ).all()
    result = [strat.strategy for strat, in strategies]
    return result


def get_strategy_translation_by_id(user, strategy_id):
    strategy = db.session.scalar(
        sa.select(StrategyTranslation).where(StrategyTranslation.strategy == strategy_id).where(
            StrategyTranslation.language_id == user.language_id))
    return strategy


def set_context_completed(user, context):
    completed_contexts = ConversationCompletedContexts(
        conversation_id=user.conversation_state.id,
        completed_context_id=context.id
    )
    db.session.add(completed_contexts)
    db.session.flush()


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
        sa.select(StrategyTranslation.id, StrategyTranslation.strategy,
                  StrategyTranslation.name, StrategyTranslation.description)
        .where(StrategyTranslation.language_id == lang_id)
    ).all()
    return strats


def get_strategies_for_context(user, context_id):
    answers = db.session.scalars(
        sa.select(UserStrategy)
        .where(UserStrategy.user == user)
        .where(UserStrategy.context == context_id)
    ).all()
    return answers


def get_strategy_mentions_for_user(user, strategy):
    strategy_mentions = db.session.scalars(
        sa.select(UserStrategy)
        .where(UserStrategy.user == user)
        .where(UserStrategy.strategy == strategy.strategy)
    ).all()
    return strategy_mentions


def first_time_setup(userid, client, language):
    language_db = get_language(language)
    user = User(id=userid, client=client, language_id=language_db.id,
                study_subject="",
                conversation_state=ConversationState(id=str(uuid.uuid4())))
    db.session.add(user)
    db.session.flush()
    created_user = db.session.scalar(
        sa.select(User)
        .where(User.id == str(userid))
        .where(User.client == client))
    return created_user


def store_study_subject(user, subject):
    user.study_subject = subject
    db.session.flush()


def set_current_context(user, context):
    user.conversation_state.current_context = context.id
    db.session.flush()


def update_current_conversation_step(user, response):
    user.conversation_state.current_conversation_step = response
    db.session.flush()


def update_current_turn(user):
    user.conversation_state.current_turn += 1
    db.session.flush()
    return user.conversation_state.current_turn


def update_most_recent_strategy_for_frequency(user, strategy):
    user.conversation_state.strategy_for_frequency = strategy.strategy
    db.session.flush()


def store_answer(user, context, message, turn):
    answer_id = str(uuid.uuid4())
    answer = InterviewAnswer(id=answer_id,
                             user=user,
                             context=context,
                             message=message,
                             turn=turn)
    db.session.add(answer)
    db.session.flush()
    created_answer = db.session.scalar(
        sa.select(InterviewAnswer).where(InterviewAnswer.id == answer_id)
    )
    return created_answer


def store_strategy(user, interview_answer, context_id, strategy_id):
    user_strategy_id = str(uuid.uuid4())
    user_strategy = UserStrategy(id=user_strategy_id,
                                 user=user,
                                 context=context_id,
                                 strategy=strategy_id,
                                 interview_answer=interview_answer)
    db.session.add(user_strategy)
    db.session.flush()
    created_user_strategy = db.session.scalar(
        sa.select(UserStrategy).where(UserStrategy.id == user_strategy_id)
    )
    return created_user_strategy


def update_strategy_with_frequency(user, context_id, strategy_id, frequency):
    strategy = db.session.scalar(
        sa.select(UserStrategy)
        .where(UserStrategy.user == user)
        .where(UserStrategy.context == context_id)
        .where(UserStrategy.strategy == strategy_id)
    )
    strategy.frequency = frequency
    logger.info("Updating strategy %s for context %s with frequency %s", strategy_id, context_id, frequency)
    db.session.flush()


def store_llm_answer(user, message, context, turn):
    answer_id = str(uuid.uuid4())
    if context:
        context_id = context.id
    else:
        context_id = None
    answer = LlmResponse(id=answer_id,
                         user=user,
                         message=message,
                         context=context_id,
                         turn=turn)
    db.session.add(answer)
    db.session.flush()
    created_answer = db.session.scalar(
        sa.select(LlmResponse).where(LlmResponse.id == answer_id)
    )
    return created_answer


def set_interview_complete(user):
    user.conversation_state.interview_completed = True
    db.session.flush()


def save_evaluation_for_strategy(user, strategy, SU, SF, SC):
    evaluation_id = str(uuid.uuid4())
    evaluation = StrategyEvaluation(id=evaluation_id,
                                    user_id=user.id,
                                    user_client=user.client,
                                    strategy=strategy.strategy,
                                    SU=SU,
                                    SF=SF,
                                    SC=SC)
    db.session.add(evaluation)
    db.session.flush()
    created_evaluation = db.session.scalar(
        sa.select(StrategyEvaluation).where(StrategyEvaluation.id == evaluation_id)
    )
    return created_evaluation


def retrieve_similar_docs_vector(query_embedding):
    embedding_array = np.array(query_embedding)
    query = sa.select(StrategyVector).order_by(StrategyVector.embedding.l2_distance(embedding_array))
    result = db.session.scalars(query.limit(5)).fetchall()
    return result


def archive_conversation(user, conversation_data):
    archive = Archive(archived_conversation=str(conversation_data))
    db.session.add(archive)
    delete_user = sa.delete(User).where(User.id == user.id).where(User.client == user.client)
    db.session.execute(delete_user)
    db.session.commit()
    return True
