import re
import json

from .db_utils.crud import get_language_by_id, get_all_strategies
from .llm import (
    get_llm_response_openai,
    get_strategy_analysis_prompt,
    get_format_strategy_prompt,
    get_format_frequency_prompt
)
from .models import User


def strategy_step(user: User, context: str, prev_conversation: list[str]):
    with open("app/config/interview.json", "r", encoding="utf-8") as file:
        interview_context = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    strat_info = []
    for category in interview_context[user_lang.lang_code]["categories"]:
        strat_info.append(category["strategies"])

    strategy_analysis_prompt = get_strategy_analysis_prompt(user)
    reasoning_response = get_llm_response_openai(strategy_analysis_prompt, user_prompt=None, temperature=0.0,
                                                 prev_conversation=prev_conversation)
    print(reasoning_response)

    limit = 6
    system_prompt = get_format_strategy_prompt(user, reasoning_response, len(prev_conversation), context, limit)

    json_output, json_valid = try_get_json_completion(5, 0.0, 0.2, system_prompt, prev_conversation=prev_conversation,
                                                      user_prompt=None)
    if not json_valid:
        return [], "in_progress", json_output
    if json_output["strategies"] in ([], ["other"]) and len(prev_conversation) >= limit:
        json_output["strategies"] = ["other"]
        json_output["status"] = "abandon"
    return json_output["strategies"], json_output["status"], json_output["comment"]


def frequency_step(user: User, prev_conversation: list[str]):
    strategy_for_frequency = user.conversation_state.strategy_for_frequency

    system_prompt = get_format_frequency_prompt(user, strategy_for_frequency)
    json_output, json_valid = try_get_json_completion(5, 0.0, 0.2, system_prompt, prev_conversation=prev_conversation,
                                                      user_prompt=None)
    if not json_valid:
        return [], 0, "in_progress", json_output
    if json_output["status"] == "in_progress" and len(prev_conversation) > 10:
        json_output["status"] = "abandon"
        json_output["frequency"] = 0
    return strategy_for_frequency, json_output["frequency"], json_output["status"], json_output["comment"]


def complete():
    pass


def validate_strategies(user_strategies):
    all_strategies = get_all_strategies()
    valid_strategies = []
    for strategy in user_strategies:
        if strategy in all_strategies:
            valid_strategies.append(strategy)
    return valid_strategies


def try_get_json_completion(
        num_attempts, start_temp, temp_increase, system_prompt, prev_conversation=[], user_prompt=None
):
    attempts = num_attempts
    temperature = start_temp
    while attempts > 0:
        try:
            llm_message = get_llm_response_openai(system_prompt, user_prompt=user_prompt, temperature=temperature,
                                                  prev_conversation=prev_conversation)
            regex = r"{[\s\S]+}"
            json_string = re.search(regex, llm_message).group()
            json_output = json.loads(json_string)
            json_valid = True
            return json_output, json_valid
        except AttributeError:
            attempts -= 1
            temperature += temp_increase
            continue

    json_valid = False
    return llm_message, json_valid
