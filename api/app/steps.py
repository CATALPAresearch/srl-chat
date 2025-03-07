import re
import json
import logging
from pydantic import BaseModel
from json.decoder import JSONDecodeError

from .db_utils.crud import get_language_by_id, get_all_strategies
from .llm import (
    get_llm_response_openai,
    get_strategy_analysis_prompt,
    get_format_strategy_prompt,
    get_frequency_validate_prompt,
    get_format_frequency_prompt,
    get_intro_prompt,
    get_prompt
)
from .models import User

ABANDON_AFTER_STEPS = 6
logger = logging.getLogger('StudyBot')


class StepIntroFields(BaseModel):
  study_subject: str
  status: str
  comment: str

def intro_step(user: User, prev_conversation: list[str]):
    intro_prompt = get_intro_prompt(user, ABANDON_AFTER_STEPS)
    system_prompt = get_prompt(user, "system")

    json_output, json_valid = try_get_json_completion(5, 0.0, 0.2, intro_prompt + system_prompt,
                                                      expected_fields=["study_subject", "status", "comment"],
                                                      expected_fields_model=StepIntroFields,
                                                      prev_conversation=prev_conversation,
                                                      user_prompt=None)
    if not json_valid:
        return "", "in_progress", json_output
    if json_output["study_subject"] == "" and len(prev_conversation) >= ABANDON_AFTER_STEPS:
        json_output["study_subject"] = ["unknown"]
        json_output["status"] = "abandon"
    return json_output["study_subject"], json_output["status"], json_output["comment"]


class StepStrategieStepperFields(BaseModel):
  strategies: str
  status: str
  comment: str

def strategy_step(user: User, context: str, prev_conversation: list[str]):
    logger.debug("Retrieving contexts")
    with open("app/config/interview.json", "r", encoding="utf-8") as file:
        interview_context = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    strat_info = []
    for category in interview_context[user_lang.lang_code]["categories"]:
        strat_info.append(category["strategies"])

    logger.debug("Retrieving prompt")
    strategy_analysis_prompt = get_strategy_analysis_prompt(user)
    logger.debug("Retrieving reasoning response")
    reasoning_response = get_llm_response_openai(strategy_analysis_prompt, user_prompt=None, temperature=0.0,
                                                 prev_conversation=prev_conversation)
    logger.debug("Retrieving prompt")
    format_strategy_prompt = get_format_strategy_prompt(user, reasoning_response, len(prev_conversation), context,
                                                        ABANDON_AFTER_STEPS)
    system_prompt = get_prompt(user, "system")
    logger.debug("Retrieving JSON")
    json_output, json_valid = try_get_json_completion(5, 0.0, 0.2, format_strategy_prompt + system_prompt,
                                                      expected_fields=["strategies", "status", "comment"],
                                                      expected_fields_model=StepStrategieStepperFields,
                                                      prev_conversation=prev_conversation,
                                                      user_prompt=None)
    if not json_valid:
        return [], "in_progress", json_output
    if json_output["strategies"] in ([], ["other"]) and len(prev_conversation) >= ABANDON_AFTER_STEPS:
        json_output["strategies"] = ["other"]
        json_output["status"] = "abandon"
    return json_output["strategies"], json_output["status"], json_output["comment"]


class StepFrequencyStepperFields(BaseModel):
  frequency: str
  status: str
  comment: str

def frequency_step(user: User, prev_conversation: list[str], conversation_for_strategy_in_context: list[str]):
    logger.debug("Retrieving strategy")
    strategy_for_frequency = user.conversation_state.strategy_for_frequency

    logger.debug("Retrieving prompt")
    frequency_validate_prompt = get_frequency_validate_prompt(user, strategy_for_frequency)
    system_prompt = get_prompt(user, "system")
    logger.debug("Retrieving reasoning response")
    reasoning_response = get_llm_response_openai(frequency_validate_prompt + system_prompt, user_prompt=None, temperature=0.0,
                                                 prev_conversation=conversation_for_strategy_in_context)
    logger.debug("Retrieving prompt")
    format_frequency_prompt = get_format_frequency_prompt(user, strategy_for_frequency, reasoning_response)
    logger.debug("Retrieving JSON")
    json_output, json_valid = try_get_json_completion(5, 0.0, 0.2, format_frequency_prompt + system_prompt,
                                                      expected_fields=["frequency", "status", "comment"],
                                                      expected_fields_model=StepFrequencyStepperFields,
                                                      prev_conversation=prev_conversation,
                                                      user_prompt=None
                                                      )
    if not json_valid:
        return [], 0, "in_progress", json_output
    if json_output["status"] == "in_progress" and len(prev_conversation) > (ABANDON_AFTER_STEPS * 2):
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
        num_attempts, start_temp, temp_increase, system_prompt, expected_fields, expected_fields_model, prev_conversation=[], user_prompt=None
):
    attempts = num_attempts
    temperature = start_temp
    while attempts > 0:
        try:
            logger.info("@ steps, try_get_json_completion:: call get_llm_response_openai")
            llm_message_raw = get_llm_response_openai(system_prompt, user_prompt=user_prompt, temperature=temperature,
                                                  prev_conversation=prev_conversation, expected_fields_model=expected_fields_model)
            regex = r"{[\s\S]+}"
            #logger.info('system_prompt',system_prompt)
            #logger.info('user_prompt',user_prompt)
            logger.info("@ steps, try_get_json_completion:: LLM response: "+llm_message_raw)
            
            json_string = re.search(regex, llm_message_raw).group()
            json_output = json.loads(json_string)
            for field in expected_fields:
                if not json_output[field]:
                    continue
            json_valid = True
            logger.info("JSON is valid")
            return json_output, json_valid
        except (AttributeError, JSONDecodeError):
            logger.info("Invalid JSON, trying again")
            attempts -= 1
            temperature += temp_increase
            continue

    json_valid = False
    logger.info("JSON invalid")
    return llm_message_raw, json_valid
