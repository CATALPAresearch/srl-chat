from collections import OrderedDict
import json
import os
from xml.sax.saxutils import escape as xmlescape
from html import escape as htmlescape

from .llm import get_llm_response_openai, eval_strategies, eval_frequencies
from .db_utils.crud import (
    get_language,
    get_language_by_id,
    get_user,
    first_time_setup,
    get_contexts,
    get_context_by_id,
    get_strategy_by_id,
    store_answer,
    set_current_context,
    set_context_completed,
    get_completed_contexts,
    update_most_recent_conversation_state,
    update_strategy_with_frequency,
    get_strategies_for_context,
    store_llm_answer,
    set_interview_complete,
    store_strategy
)

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
    update_most_recent_conversation_state(user, "getstrategies")

    llm_message = get_llm_response_openai(MODEL, system_prompt + " " + start_prompt, "Lass uns loslegen", 0.1)

    return llm_message, 200


def reply_core(client, userid, user_message) -> tuple[str, int]:
    """
    Post request format:
    {
        "client": "discord",
        "userid": Discord user ID
        "user_message": message
    }
    """
    user = get_user(userid, client)
    if user is None:
        raise FileNotFoundError("User not found")
        # language = "en"  # TODO - ask first time
        # return start_conversation(language, client, userid)

    # Retrieve current context
    current_context_id = user.conversation_state.current_context
    current_context = get_context_by_id(current_context_id)
    user_answer_db = store_answer(user, current_context.id, user_message)

    if user.conversation_state.interview_completed:
        return sign_off_interview(user)

    match user.conversation_state.most_recent_response:
        case "getstrategies":
            llm_message = evaluate_strategies(user, user_message, current_context, user_answer_db)
        case "probe":
            llm_message = evaluate_strategies(user, user_message, current_context, user_answer_db, probe=False)
        case "frequency":
            # evaluate and store indicated frequency of strategy use
            frequency_json = eval_frequencies(user, user_message)
            # Store user's answer(s)
            update_strategy_with_frequency(user, current_context_id, frequency_json["strategy"], frequency_json["frequency"])
            # check if further strategies need to be checked for frequency
            llm_message = ask_about_frequency(user, current_context)
        case _:
            pass

    store_llm_answer(user, llm_message)
    return llm_message, 200


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


def get_prompt(user, prompt_name):
    with open("app/config/prompts.json", "r", encoding="utf-8") as file:
        prompts = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    prompt = prompts[user_lang.lang_code][prompt_name]
    return prompt


def get_probe_prompt(context, user):
    prompt = get_prompt(user, "probe")
    prompt = prompt.replace("${context}", context)
    return prompt


def get_context_prompt(context, user):
    prompt = get_prompt(user, "context")
    prompt = prompt.replace("${context}", context)
    return prompt


def get_system_prompt(user):
    return get_prompt(user, "system")


def get_start_prompt(context, user):
    prompt = get_prompt(user, "start")
    prompt = prompt.replace("${context}", str(context))
    return prompt


def get_eval_prompt(strategies, user_message, user):
    prompt = get_prompt(user, "eval")
    prompt = prompt.replace("${strategies}", str(strategies)).replace("${user_message}", user_message)
    return prompt


def get_frequency_prompt(user, context, strategy):
    prompt = get_prompt(user, "frequency")
    prompt = prompt.replace("${strategy}", str(strategy)).replace("${context}", context)
    return prompt


def get_eval_frequency_prompt(user, user_message):
    prompt = get_prompt(user, "eval_frequency")
    prompt = prompt.replace("${user_message}", str(user_message))
    return prompt


def start_conversation(language, client, userid):
    """
    Post request format:
    {
        "language": "en" or "de",
        "client": "discord",
        "userid": Discord user ID
    }
    """
    with open("app/config/translations.json", "r", encoding="utf-8") as file:
        translations = json.load(file)
    with open("app/config/interview.json", "r", encoding="utf-8") as file:
        interview_context = json.load(file)

    if not get_language(language):
        msg = translations["language_not_supported_message"]
        response = xmlescape(msg, {"ä": "&auml;", "ö": "&ouml;", "ü": "&uuml;"})
        return htmlescape(response), 400

    created_user = first_time_setup(userid, client, language)
    if created_user is None:
        return "An error occurred, please try to restart the conversation", 500

    system_prompt = get_system_prompt(created_user)
    start_prompt = get_start_prompt(interview_context[language]["contexts"][0], created_user)

    llm_message = get_llm_response_openai(MODEL, system_prompt + " " + start_prompt, "", 0.1)

    return llm_message


def retrieve_full_conversation(user):
    conversation = {}
    for response in user.llm_responses:
        conversation[response.message_time] = {"role": "assistant", "content": response.message}
    for response in user.interview_answers:
        conversation[response.message_time] = {"role": "user", "content": response.message}
    ordered_conversation = OrderedDict(sorted(conversation.items()))

    messages = []
    for timestamp, data in ordered_conversation.items():
        messages.append(data)

    return messages


def evaluate_strategies(user, user_message, current_context, user_answer_db, probe=True):
    (analysis, identified_strategy_array) = eval_strategies(user, user_message)
    store_llm_answer(user, analysis)
    # Identify ID of "other" strategy (corresponding to no concrete strategy mentioned)
    no_strategy_mentioned = []
    # Store user's answer(s)
    if not type(identified_strategy_array) == list:
        identified_strategy_array = [identified_strategy_array]
    for identified_strategy in identified_strategy_array:
        store_strategy(user, user_answer_db, current_context.id, identified_strategy["index"])
        if identified_strategy["strategy"] == "other":
            no_strategy_mentioned.append(1)

    if no_strategy_mentioned == [1]:
        if probe:
            # Probe further if only "other" strategy identified
            probe_prompt = get_probe_prompt(current_context.context, user)
            update_most_recent_conversation_state(user, "probe")
            conversation_so_far = retrieve_full_conversation(user)
            system_prompt = get_system_prompt(user)
            llm_message = get_llm_response_openai(MODEL, system_prompt + " " + probe_prompt, "", 0.0, conversation_so_far)
        else:
            # Move on if we've already probed
            llm_message = move_to_next_context(user, current_context)
    else:
        llm_message = ask_about_frequency(user, current_context)

    return llm_message


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
            update_most_recent_conversation_state(user, "frequency")
            conversation_so_far = retrieve_full_conversation(user)
            llm_message = get_llm_response_openai(MODEL, system_prompt + " " + frequency_prompt, "", 0.0, conversation_so_far)
            break
    # if all answers have frequency, move to next context
    else:
        llm_message = move_to_next_context(user, current_context)
    return llm_message


def move_to_next_context(user, current_context):
    next_context = set_current_context_complete(user, current_context.id)
    conversation_so_far = retrieve_full_conversation(user)
    system_prompt = get_system_prompt(user)
    if next_context:
        prompt = get_context_prompt(next_context.context, user)
        update_most_recent_conversation_state(user, "getstrategies")
        llm_message = get_llm_response_openai(MODEL, system_prompt + " " + prompt, "", 0.0, conversation_so_far)
    else:
        update_most_recent_conversation_state(user, "complete")
        llm_message = sign_off_interview(user)

    return llm_message


def sign_off_interview(user):
    prompt = get_prompt(user, "interview_complete")
    system_prompt = get_system_prompt(user)
    llm_message = get_llm_response_openai(MODEL, system_prompt + " " + prompt, "", 0.0)
    return llm_message
