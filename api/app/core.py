from collections import OrderedDict
import json
import os
from xml.sax.saxutils import escape as xmlescape

from .llm import (
    get_llm_response_openai,
    get_system_prompt,
    get_start_prompt,
    get_frequency_prompt,
    get_context_prompt,
    get_complete_prompt)
from .db_utils.crud import (
    get_language,
    get_user,
    first_time_setup,
    get_contexts,
    get_context_by_id,
    get_strategy_by_id,
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
    update_most_recent_strategy_for_frequency
)
from .steps import strategy_step, frequency_step, probe_step, format_strategy

MODEL = os.getenv("MODEL")


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

        contexts = set(get_contexts(user.language_id))

        if get_completed_contexts(user) is not None:
            completed_contexts = set(get_completed_contexts(user))
            remaining_contexts = contexts.difference(completed_contexts)
        else:
            remaining_contexts = contexts
        current_context = list(remaining_contexts)[0]

        set_current_context(user, current_context)

        system_prompt = get_system_prompt(user)
        start_prompt = get_start_prompt(current_context.context, user)
        update_current_conversation_step(user, "strategy")

        llm_message = get_llm_response_openai(system_prompt + " " + start_prompt, "Hi!", 0.1)
        turn = update_current_turn(user)
        store_llm_answer(user, llm_message, current_context, turn)
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
        current_context = get_context_by_id(current_context_id)
        turn = update_current_turn(user)
        user_answer_db = store_answer(user, current_context.id, user_message, turn)

        conversation_for_current_context = retrieve_full_conversation(user, current_context.id)

        if user.conversation_state.interview_completed:
            return sign_off_interview(user)

        match user.conversation_state.current_conversation_step:
            case "strategy":
                strategies_mentioned, status, llm_message = strategy_step(user, str(current_context.context),
                                                                          conversation_for_current_context)
                if status == "completed":
                    update_current_conversation_step(user, "frequency")
                    for mentioned_strategy in strategies_mentioned:
                        strategy_index = format_strategy(user, mentioned_strategy)
                        store_strategy(user, user_answer_db, current_context.id, strategy_index)
                    llm_message, current_context = ask_about_frequency(user, current_context)
                elif status == "in_progress" and strategies_mentioned == ["other"]:
                    update_current_conversation_step(user, "probe")
            case "probe":
                strategies_mentioned, status = probe_step(user, conversation_for_current_context)
                for mentioned_strategy in strategies_mentioned:
                    strategy_index = format_strategy(user, mentioned_strategy)
                    store_strategy(user, user_answer_db, current_context.id, strategy_index)
                    if strategy_index in (13, 26):
                        update_strategy_with_frequency(user, current_context.id, strategy_index, 0)
                llm_message, current_context = ask_about_frequency(user, current_context)
            case "frequency":
                strategy_rated, rated_frequency, status, llm_message = frequency_step(user,
                                                                                      conversation_for_current_context)
                if status == "completed":
                    # Store user's answer(s)
                    update_strategy_with_frequency(user, current_context_id, strategy_rated,
                                                   rated_frequency)
                    # check if further strategies need to be checked for frequency
                    llm_message, current_context = ask_about_frequency(user, current_context)
            case _:
                pass

        turn = update_current_turn(user)
        store_llm_answer(user, llm_message, current_context, turn)
        return llm_message, 200
    except Exception as e:
        raise Exception(e)


def set_current_context_complete(user, current_context):
    # Set context completed and move to next context
    contexts = set(get_contexts(user.language_id))
    print(current_context, current_context.id)
    set_context_completed(user, current_context)
    print("w")
    completed_contexts = set(get_completed_contexts(user))
    print("aaaa")
    remaining_contexts = contexts.difference(completed_contexts)
    print(remaining_contexts)
    if remaining_contexts == set():
        set_interview_complete(user)
        return None

    print(list(remaining_contexts))
    next_context = list(remaining_contexts)[0]
    set_current_context(user, next_context)
    print(next_context)
    return next_context


def retrieve_full_conversation(user, context_id=None):
    conversation = {}
    for response in user.llm_responses:
        if context_id is None or response.context == context_id:
            conversation[response.turn] = {"role": "assistant", "content": response.message}
    for response in user.interview_answers:
        if context_id is None or response.context == context_id:
            conversation[response.turn] = {"role": "user", "content": response.message}
    ordered_conversation = OrderedDict(sorted(conversation.items()))

    messages = []
    for turn, data in ordered_conversation.items():
        messages.append(data)

    return messages


def ask_about_frequency(user, current_context):
    # retrieve all interview answers for current context
    answers = get_strategies_for_context(user, current_context.id)
    system_prompt = get_system_prompt(user)

    def list_filter(a):
        other_strategy_indices = [13, 26]
        if a.frequency is None and a.strategy not in other_strategy_indices:
            return True
        else:
            return False

    answers_without_frequency = list(filter(list_filter, answers))
    if len(answers_without_frequency):
        for answer in answers_without_frequency:
            context = get_context_by_id(answer.context)
            strategy = get_strategy_by_id(answer.strategy)
            frequency_prompt = get_frequency_prompt(user, context.context, strategy.strategy)
            update_current_conversation_step(user, "frequency")
            update_most_recent_strategy_for_frequency(user, strategy)
            conversation_so_far = retrieve_full_conversation(user)
            llm_message = get_llm_response_openai(system_prompt + " " + frequency_prompt,
                                                  prev_conversation=conversation_so_far)
            new_context = current_context
            break
    # if all answers have frequency, move to next context
    else:
        llm_message, new_context = move_to_next_context(user, current_context)
    return llm_message, new_context


def move_to_next_context(user, current_context):
    next_context = set_current_context_complete(user, current_context)

    system_prompt = """You are an interviewer conducting an interview that will be evaluated scientifically. 
    Your tone should be friendly but neutral. """
    if next_context:
        prompt = get_context_prompt(next_context.context, user)
        update_current_conversation_step(user, "strategy")
        llm_message = get_llm_response_openai(system_prompt + " " + prompt)
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
    for strategy in get_strategies(user.language_id):
        strategy_scores[strategy.id] = {"contexts": []}
        mentions = get_strategy_mentions_for_user(user, strategy)
        SU = 0
        SF = 0
        SC = 0
        if mentions:
            SU = (len(mentions) != 0)
            SF = len(mentions)
            for mention in mentions:
                SC += mention.frequency
                strategy_scores[strategy.id]["contexts"].append(mention.context)
        evaluation = save_evaluation_for_strategy(user, strategy, SU, SF, SC)
        strategy_scores[strategy.id]["SU"] = SU
        strategy_scores[strategy.id]["SF"] = SF
        strategy_scores[strategy.id]["SC"] = SC
        if SF != 0:
            strategy_scores[strategy.id]["RC"] = SC / SF
        else:
            strategy_scores[strategy.id]["RC"] = 0
        evaluations.append(evaluation)
    summary = generate_summary(user, strategy_scores)
    return summary


def generate_summary(user, strategy_scores):
    most_contexts = list(sorted(strategy_scores.items(), key=lambda item: len(item[1]["contexts"]), reverse=True))
    most_consistently = list(sorted(strategy_scores.items(), key=lambda item: item[1]["RC"], reverse=True))
    strategies_used = list({strategy: item for strategy, item in strategy_scores.items() if len(item["contexts"]) > 0})
    consistently_used = list({strategy: item for strategy, item in strategy_scores.items() if item["RC"] > 2.5})

    most_contexts_strat = get_strategy_by_id(most_contexts[0][0]).strategy
    const_strategy = get_strategy_by_id(most_consistently[0][0]).strategy
    avg_freq = most_consistently[0][1]["RC"]
    total_strat = len(strategies_used)
    const_strategies = []
    for strat in consistently_used:
        const_strategies.append(get_strategy_by_id(strat).strategy)
    conversation_so_far = retrieve_full_conversation(user)
    system_prompt = get_system_prompt(user)
    prompt = get_complete_prompt(user, most_contexts_strat, const_strategy, avg_freq, total_strat, const_strategies)
    llm_message = get_llm_response_openai(system_prompt + " " + prompt, prev_conversation=conversation_so_far)
    return llm_message
