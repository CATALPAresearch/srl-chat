import os
from json import JSONDecodeError

from app import app, db
from app.models import User, Language

from flask import request
import json
import sqlalchemy as sa
from xml.sax.saxutils import escape as xmlescape
from html import escape as htmlescape
from autogen import AssistantAgent, ConversableAgent, GroupChat, GroupChatManager, UserProxyAgent

from app.llm import get_llm_response_openai
from db_utils.crud import (
    get_language,
    get_language_by_id,
    get_user,
    first_time_setup,
    get_strategies,
    get_contexts,
    get_context_by_id,
    get_strategy_by_id,
    store_answer,
    set_current_context,
    set_context_completed,
    get_completed_contexts,
    update_most_recent_response,
    update_answer_with_frequency,
    get_answers_for_context,
    store_llm_answer
)

OPENROUTER_HOST = "https://openrouter.ai/api/v1"
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")


@app.route('/')
def index():
    return "OK"

@app.route("/startConversation", methods=['POST'])
def start_conversation():
    """
    Post request format:
    {
        "language": "en" or "de",
        "client": "discord",
        "userid": Discord user ID
    }
    """
    with open("config/translations.json") as file:
        translations = json.load(file)
    content = request.json
    language = content["language"]
    client = content["client"]
    userid = content["userid"]

    if not get_language(language):
        msg = translations["language_not_supported_message"]
        response = xmlescape(msg, {"ä": "&auml;", "ö": "&ouml;", "ü": "&uuml;"})
        return htmlescape(response), 400

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

    start_prompt = get_start_prompt(current_context.context, user)
    update_most_recent_response(user, "getstrategies")

    llm_message = get_llm_response_openai("mistralai/mixtral-8x22b-instruct", start_prompt, "Lass uns loslegen", 0.1)

    return llm_message


@app.route("/reply", methods=['POST'])
def reply():
    """
    Post request format:
    {
        "client": "discord",
        "userid": Discord user ID
        "message": message
    }
    """
    content = request.json
    client = content["client"]
    userid = content["userid"]
    user_message = content["message"]

    user = get_user(userid, client)
    if user is None:
        language = "en" # TODO - ask first time
        return start_conversation(language, client, userid)

    if user.conversation_state.interview_completed:
        pass

    # Retrieve current context
    current_context_id = user.conversation_state.current_context
    current_context = get_context_by_id(current_context_id)

    match user.conversation_state.most_recent_response:
        case "getstrategies":
            identified_strategy_array = eval_strategies(user, user_message)
            # Identify ID of "other" strategy (corresponding to no concrete strategy mentioned)
            no_strategy_mentioned = []
            # Store user's answer(s)
            if not type(identified_strategy_array) == list:
                identified_strategy_array = [identified_strategy_array]
            for identified_strategy in identified_strategy_array:
                store_answer(user, current_context_id, identified_strategy["index"], user_message)
                if identified_strategy["strategy"] == "other":
                    no_strategy_mentioned.append(1)

            if no_strategy_mentioned == [1]:
                # Probe further if only "other" strategy identified
                probe_prompt = get_probe_prompt(current_context.context, user)
                update_most_recent_response(user, "probe")
                llm_message = get_llm_response_openai("mistralai/mixtral-8x22b-instruct", probe_prompt, "", 0.0)
            else:
                # retrieve all interview answers for current context
                answers = get_answers_for_context(user, current_context_id)
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
                        update_most_recent_response(user, "frequency")
                        llm_message = get_llm_response_openai("mistralai/mixtral-8x22b-instruct", frequency_prompt, "", 0.0)
                        break
                # if all answers have frequency, move to next context
                else:
                    next_context = set_current_context_complete(user, current_context_id)
                    context_prompt = get_context_prompt(next_context.context, user)
                    update_most_recent_response(user, "getstrategies")
                    llm_message = get_llm_response_openai("mistralai/mixtral-8x22b-instruct", context_prompt, "", 0.0)

        case "probe":
            identified_strategy_array = eval_strategies(user, user_message)
            # Identify ID of "other" strategy (corresponding to no concrete strategy mentioned)
            no_strategy_mentioned = []
            # Store user's answer(s)
            if not type(identified_strategy_array) == list:
                identified_strategy_array = [identified_strategy_array]
            for identified_strategy in identified_strategy_array:
                store_answer(user, current_context_id, identified_strategy["index"], user_message)
                if identified_strategy["strategy"] == "other":
                    no_strategy_mentioned.append(1)
            if identified_strategy_array["strategy"] == "other":
                next_context = set_current_context_complete(user, current_context_id)
                context_prompt = get_context_prompt(next_context.context, user)
                update_most_recent_response(user, "getstrategies")
                llm_message = get_llm_response_openai("mistralai/mixtral-8x22b-instruct", context_prompt, "", 0.0)
            else:
                frequency_prompt = get_frequency_prompt(user, current_context.context, identified_strategy_array)
                update_most_recent_response(user, "frequency")
                llm_message = get_llm_response_openai("mistralai/mixtral-8x22b-instruct", frequency_prompt, "", 0.0)

        case "frequency":
            # evaluate and store indicated frequency of strategy use
            frequency_json = eval_frequencies(user, user_message)
            # Identify ID of "other" strategy (corresponding to no concrete strategy mentioned)
            no_strategy_mentioned = []
            # Store user's answer(s)
            update_answer_with_frequency(user, current_context_id, frequency_json["strategy"], frequency_json["frequency"])

            # check if further strategies need to be checked for frequency
            # retrieve all interview answers for current context
            answers = get_answers_for_context(user, current_context_id)

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
                    update_most_recent_response(user, "frequency")
                    llm_message = get_llm_response_openai("mistralai/mixtral-8x22b-instruct", frequency_prompt, "", 0.0)
                    break
            # if all answers have frequency set, move to next context
            else:
                next_context = set_current_context_complete(user, current_context_id)
                context_prompt = get_context_prompt(next_context.context, user)
                update_most_recent_response(user, "getstrategies")
                llm_message = get_llm_response_openai("mistralai/mixtral-8x22b-instruct", context_prompt, "", 0.0)

        case _:
            pass

    store_llm_answer(user, llm_message)
    return llm_message


def eval_strategies(user, user_message):
    """
    Evaluate if user response mentions any strategies.
    """
    strategies = get_strategies(user.language_id)
    config_list_read = [
        {
            "model": "meta-llama/llama-3.1-8b-instruct",
            "base_url": OPENROUTER_HOST,
            "api_key": OPENROUTER_KEY,
        }
    ]
    config_list_code = [
        {
            "model": "nousresearch/hermes-2-pro-llama-3-8b",
            "base_url": OPENROUTER_HOST,
            "api_key": OPENROUTER_KEY,
        }
    ]
    strategy_recogniser = AssistantAgent(
        name="Recognise_strategy",
        llm_config={"config_list": config_list_read},
        system_message=f"""Read the user message and decide whether they have mentioned one or several strategies from 
        the following list: {strategies}, then state what strategies they are.""",
    )
    strategy_formatter = AssistantAgent(
        name="Reformat_strategy",
        llm_config={"config_list": config_list_code},
        system_message=f"""Reformat the learning strategies employed by the user to json. Take strategy metadata from 
        the following information: {strategies}. Output only an array of strategies, with each strategy given in the 
        following format, and include no other content in your message:
         {{"index": <index as number>, "strategy": <name of strategy>}}.""",
    )

    initializer = UserProxyAgent(
        name="Init",
        code_execution_config=False
    )
    chat_results = initializer.initiate_chats(
        [
            {
                "recipient": strategy_recogniser,
                "message": user_message,
                "max_turns": 1,
                "summary_method": "last_msg",
            },
            {
                "recipient": strategy_formatter,
                "message": "Please reformat the strategies we have recognised.",
                "max_turns": 1,
                "summary_method": "last_msg",
            },
        ]
    )
    print(chat_results)
    print("***********************")
    print(chat_results[-1].summary)
    return json.loads(chat_results[-1].summary)


def eval_frequencies(user, user_message):
    """
    Evaluate frequency of strategy use mentioned in most recent user response
    for context asked for in most recent LLM message.
    """
    strategies = get_strategies(user.language_id)
    most_recent_response = user.llm_responses[0]
    for response in user.llm_responses:
        if response.message_time >= most_recent_response.message_time:
            most_recent_response = response

    config_list_read = [
        {
            "model": "mistralai/mixtral-8x22b",
            "base_url": OPENROUTER_HOST,
            "api_key": OPENROUTER_KEY,
        }
    ]
    config_list_code = [
        {
            "model": "meta-llama/codellama-34b-instruct",
            "base_url": OPENROUTER_HOST,
            "api_key": OPENROUTER_KEY,
        }
    ]
    frequency_eval = AssistantAgent(
        name="Evaluate_frequency",
        llm_config={"config_list": config_list_code},
        system_message=f"""Evaluate the user's answer. Determine whether the answer mentions a 
        number between 1 and 4 and reply with that number as the frequency number and the number of 
        the strategy in the following format: {{"strategy": <Index of strategy>, "frequency": <Frequency number>}}.
        """,
    )
    context_eval = AssistantAgent(
        name="Evaluate_context",
        llm_config={"config_list": config_list_read},
        system_message=f"""Give back the index of the strategy this message talks about 
        based on the following list: {strategies}. Your response should be a single number.""",
    )

    initializer = UserProxyAgent(
        name="Init",
        code_execution_config=False
    )
    chat_results = initializer.initiate_chats(
        [
            {
                "recipient": context_eval,
                "message": most_recent_response.message,
                "max_turns": 1,
                "summary_method": "last_msg",
            },
            {
                "recipient": frequency_eval,
                "message": user_message,
                "max_turns": 1,
                "summary_method": "last_msg",
            },
        ]
    )
    print(chat_results)
    print("***********************")
    print(chat_results[-1].summary)
    return json.loads(chat_results[-1].summary)


def set_current_context_complete(user, current_context):
    # Set context completed and move to next context
    contexts = set(get_contexts(user.language_id))
    set_context_completed(user, current_context)

    completed_contexts = set(get_completed_contexts(user))
    remaining_contexts = contexts.difference(completed_contexts)
    if remaining_contexts == set():
        return "Interview complete"

    next_context = list(remaining_contexts)[0]
    set_current_context(user, next_context)
    return next_context


def get_prompt(user, prompt_name):
    with open("config/prompts.json") as file:
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
    with open("config/translations.json") as file:
        translations = json.load(file)
    with open("config/interview.json") as file:
        interview_context = json.load(file)

    if not get_language(language):
        msg = translations["language_not_supported_message"]
        response = xmlescape(msg, {"ä": "&auml;", "ö": "&ouml;", "ü": "&uuml;"})
        return htmlescape(response), 400

    created_user = first_time_setup(userid, client, language)
    if created_user is None:
        return "An error occurred, please try to restart the conversation", 500

    start_prompt = get_start_prompt(interview_context[language]["contexts"][0], created_user)

    llm_message = get_llm_response_openai("mistralai/mixtral-8x22b-instruct", start_prompt, "", 0.1)

    return llm_message
