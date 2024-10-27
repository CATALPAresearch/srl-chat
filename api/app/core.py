from collections import OrderedDict
import json
import os
from xml.sax.saxutils import escape as xmlescape
import logging

from .llm import (
    get_llm_response_openai,
    get_prompt,
    get_frequency_prompt,
    get_context_prompt,
    get_complete_prompt)
from .db_utils.crud import (
    get_language,
    get_user,
    first_time_setup,
    get_contexts,
    get_context_by_id,
    get_strategy_translation_by_id,
    store_answer,
    set_current_context,
    set_context_completed,
    get_completed_contexts,
    update_current_conversation_step,
    update_current_turn,
    update_strategy_with_frequency,
    get_strategies_for_context,
    store_llm_answer,
    set_interview_complete,
    store_strategy,
    get_strategies,
    get_strategy_mentions_for_user,
    save_evaluation_for_strategy,
    update_most_recent_strategy_for_frequency,
    store_study_subject,
    archive_conversation
)
from .steps import strategy_step, frequency_step, validate_strategies, intro_step

MODEL = os.getenv("MODEL")
logger = logging.getLogger("StudyBot")


def start_conversation_core(language, client, userid) -> tuple[str, int]:
    """
    Post request format:
    {
        "language": "en" or "de",
        "client": "discord",
        "userid": Discord user ID
    }
    Returns: tuple[message, status code]
    """
    try:
        with open("app/config/translations.json", "r", encoding="utf-8") as file:
            translations = json.load(file)

        if not get_language(language):
            msg = translations["language_not_supported_message"]
            response = xmlescape(msg, {"ä": "&auml;", "ö": "&ouml;", "ü": "&uuml;"})
            return response, 400

        user = get_user(userid, client)

        if user is None:
            created_user = first_time_setup(userid, client, language)
            if created_user is None:
                return "An error occurred, please try to restart the conversation", 500
            user = created_user

        logger.info("Created new user (%s): %s - %s", language, user.id, user.client)

        system_prompt = get_prompt(user, "system")
        intro_prompt = get_prompt(user, "intro")
        update_current_conversation_step(user, "intro")

        llm_message = get_llm_response_openai(system_prompt + " " + intro_prompt, None, 0.1)
        turn = update_current_turn(user)
        store_llm_answer(user, llm_message, None, None, turn, step="intro")
        return llm_message, 200
    except Exception as e:
        raise Exception(e)


def reply_core(client, userid, user_message) -> tuple[str, int]:
    """
    Post request format:
    {
        "client": "discord",
        "userid": Discord user ID
        "user_message": message
    }
    """
    try:
        user = get_user(userid, client)
        if user is None:
            raise FileNotFoundError("User not found")
            # language = "en"  # TODO - ask first time
            # return start_conversation(language, client, userid)

        # Retrieve current context
        current_context_id = user.conversation_state.current_context
        if current_context_id:
            current_context = get_context_by_id(current_context_id)
        else:
            current_context = None
        turn = update_current_turn(user)
        conversation_step = user.conversation_state.current_conversation_step
        current_strategy = user.conversation_state.strategy_for_frequency
        user_answer_db = store_answer(user, current_context_id, current_strategy, user_message, turn, conversation_step)

        conversation_for_current_context = retrieve_full_conversation(user, current_context_id)
        logger.info(user_message)
        if user.conversation_state.interview_completed:
            return sign_off_interview(user)
        logger.info("Replying to user: %s - %s. Step: %s", user.id, user.client, conversation_step)
        match conversation_step:
            case "intro":
                study_subject, status, llm_message = intro_step(user, conversation_for_current_context)
                if status in ("completed", "complete", "abandon"):
                    store_study_subject(user, study_subject)
                    contexts = set(get_contexts(user.language_id))
                    if get_completed_contexts(user) is not None:
                        completed_contexts = set(get_completed_contexts(user))
                        remaining_contexts = contexts.difference(completed_contexts)
                    else:
                        remaining_contexts = contexts
                    current_context = list(remaining_contexts)[0]

                    set_current_context(user, current_context)

                    system_prompt = get_prompt(user, "system")
                    context_prompt = get_context_prompt(current_context.context, user)
                    update_current_conversation_step(user, "strategy")

                    llm_message = get_llm_response_openai(context_prompt + " " + system_prompt, None, 0.1)
            case "strategy":
                strategies_mentioned, status, llm_message = strategy_step(user, str(current_context.context),
                                                                          conversation_for_current_context)
                if status in ("completed", "complete", "abandon"):
                    update_current_conversation_step(user, "frequency")
                    valid_strategies = validate_strategies(strategies_mentioned)
                    for mentioned_strategy in valid_strategies:
                        store_strategy(user, user_answer_db, current_context.id, mentioned_strategy)
                        if mentioned_strategy == "008-001":
                            update_strategy_with_frequency(user, current_context.id, mentioned_strategy, 0)
                    llm_message, current_context = ask_about_frequency(user, current_context)
            case "frequency":
                conversation_for_strategy_in_context = retrieve_full_conversation(user,
                                                                                  user.conversation_state.current_context,
                                                                                  user.conversation_state.strategy_for_frequency)
                strategy_rated, rated_frequency, status, llm_message = frequency_step(user,
                                                                                      conversation_for_current_context,
                                                                                      conversation_for_strategy_in_context)
                if status in ("completed", "abandon"):
                    # Store user's answer(s)
                    update_strategy_with_frequency(user, current_context_id, strategy_rated,
                                                   rated_frequency)
                    # check if further strategies need to be checked for frequency
                    llm_message, current_context = ask_about_frequency(user, current_context)
            case _:
                pass

        turn = update_current_turn(user)
        store_llm_answer(user, llm_message, current_context,
                         user.conversation_state.strategy_for_frequency, turn,
                         user.conversation_state.current_conversation_step
                         )
        return llm_message, 200
    except Exception as e:
        raise Exception(e)


def set_current_context_complete(user, current_context):
    # Set context completed and move to next context
    contexts = set(get_contexts(user.language_id))
    set_context_completed(user, current_context)
    completed_contexts = set(get_completed_contexts(user))
    remaining_contexts = contexts.difference(completed_contexts)
    if remaining_contexts == set():
        set_interview_complete(user)
        return None

    next_context = list(remaining_contexts)[0]
    set_current_context(user, next_context)
    return next_context


def retrieve_full_conversation(user, context_id=None, step=None, strategy_id=None):
    conversation = {}
    for response in user.llm_responses:
        if context_id is None or response.context == context_id:
            if step is None or response.conversation_step == step:
                if strategy_id is None or response.strategy == strategy_id:
                    conversation[response.turn] = {"role": "assistant", "content": response.message}
    for response in user.interview_answers:
        if context_id is None or response.context == context_id:
            if step is None or response.conversation_step == step:
                if strategy_id is None or response.strategy == strategy_id:
                    conversation[response.turn] = {"role": "user", "content": response.message}
    ordered_conversation = OrderedDict(sorted(conversation.items()))

    messages = []
    for turn, data in ordered_conversation.items():
        messages.append(data)

    return messages


def ask_about_frequency(user, current_context):
    # retrieve all interview answers for current context
    answers = get_strategies_for_context(user, current_context.id)
    system_prompt = get_prompt(user, "system")

    def list_filter(a):
        if a.frequency is None and a.strategy != "008-001":
            return True
        else:
            return False

    answers_without_frequency = list(filter(list_filter, answers))
    if len(answers_without_frequency):
        for answer in answers_without_frequency:
            context = get_context_by_id(answer.context)
            strategy = get_strategy_translation_by_id(user, answer.strategy)
            logger.info("Asking about frequency for strategy: %s", strategy.name)
            frequency_prompt = get_frequency_prompt(user, context.context, strategy.name)
            update_current_conversation_step(user, "frequency")
            update_most_recent_strategy_for_frequency(user, strategy)
            conversation_so_far = retrieve_full_conversation(user, context.id, "strategy")
            llm_message = get_llm_response_openai(frequency_prompt + " " + system_prompt,
                                                  prev_conversation=conversation_so_far)
            new_context = current_context
            break
    # if all answers have frequency, move to next context
    else:
        llm_message, new_context = move_to_next_context(user, current_context)
    return llm_message, new_context


def move_to_next_context(user, current_context):
    next_context = set_current_context_complete(user, current_context)
    conversation_so_far = retrieve_full_conversation(user)
    system_prompt = get_prompt(user, "system")
    if next_context:
        logger.info("Moving on to context: %s", next_context.context)
        prompt = get_context_prompt(next_context.context, user)
        update_current_conversation_step(user, "strategy")
        llm_message = get_llm_response_openai(prompt + system_prompt,
                                              prev_conversation=conversation_so_far)
    else:
        update_current_conversation_step(user, "complete")
        llm_message = sign_off_interview(user)

    return llm_message, next_context


def sign_off_interview(user):
    summary = evaluate(user)
    return summary


def evaluate(user):
    evaluations = []
    strategy_scores = {}
    for strategy_translation in get_strategies(user.language_id):
        strategy_scores[strategy_translation.strategy] = {"contexts": []}
        mentions = get_strategy_mentions_for_user(user, strategy_translation)
        SU = 0
        SF = 0
        SC = 0
        if mentions:
            SU = (len(mentions) != 0)
            SF = len(mentions)
            for mention in mentions:
                SC += mention.frequency
                strategy_scores[strategy_translation.strategy]["contexts"].append(mention.context)
        evaluation = save_evaluation_for_strategy(user, strategy_translation, SU, SF, SC)
        strategy_scores[strategy_translation.strategy]["SU"] = SU
        strategy_scores[strategy_translation.strategy]["SF"] = SF
        strategy_scores[strategy_translation.strategy]["SC"] = SC
        if SF != 0:
            strategy_scores[strategy_translation.strategy]["RC"] = SC / SF
        else:
            strategy_scores[strategy_translation.strategy]["RC"] = 0
        evaluations.append(evaluation)
    summary = generate_summary(user, strategy_scores)
    return summary


def generate_summary(user, strategy_scores):
    most_contexts = list(sorted(strategy_scores.items(), key=lambda item: len(item[1]["contexts"]), reverse=True))
    most_consistently = list(sorted(strategy_scores.items(), key=lambda item: item[1]["RC"], reverse=True))
    strategies_used = list({strategy: item for strategy, item in strategy_scores.items() if len(item["contexts"]) > 0})
    consistently_used = list({strategy: item for strategy, item in strategy_scores.items() if item["RC"] > 2.5})

    most_contexts_strat = get_strategy_translation_by_id(user, most_contexts[0][0]).description
    const_strategy = get_strategy_translation_by_id(user, most_consistently[0][0]).description
    avg_freq = most_consistently[0][1]["RC"]
    total_strat = len(strategies_used)
    const_strategies = []
    for strat in consistently_used:
        const_strategies.append(get_strategy_translation_by_id(user, strat).description)
    full_conversation = retrieve_full_conversation(user)
    system_prompt = get_prompt(user, "system")
    prompt = get_complete_prompt(user, most_contexts_strat, const_strategy, avg_freq, total_strat, const_strategies)
    llm_message = get_llm_response_openai(prompt + " " + system_prompt, prev_conversation=full_conversation)
    return llm_message


def reset_conversation(user):
    conversation = retrieve_full_conversation(user)
    state = user.conversation_state
    archive = {"messages": conversation,
               "state": {
                   "complete": state.interview_completed,
                   "current_context": state.current_context,
                   "step": state.current_conversation_step
               }
               }
    return archive_conversation(user, archive)
