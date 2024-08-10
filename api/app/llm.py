import json
import os
import re
import requests
from openai import OpenAI
from autogen import AssistantAgent, UserProxyAgent
from .db_utils.crud import get_strategies, get_language_by_id, get_contexts_content, get_strategies_content
import logging

OLLAMA_API_URL = "http://132.176.10.80/api"
OLLAMA_HOST = "http://132.176.10.80/v1"

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")
CONFIG_LIST = [
    {
        "model": MODEL,
        "base_url": BASE_URL,
        "api_key": API_KEY,
    }
]

logger = logging.getLogger(__name__)


def get_llm_message(model, prompt, temperature):
    data = dict(model=model, prompt=prompt, stream=False, options={
        "temperature": temperature
    })
    response = requests.post(f"{OLLAMA_API_URL}/generate", data=json.dumps(data))
    print(response.content)
    response_json = json.loads(response.content.decode('utf8'))
    return response_json["response"]


def get_llm_response_openai(model, system_prompt, user_prompt=None, temperature=0.0, prev_conversation=[]):
    client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    )

    messages = [{"role": "system", "content": system_prompt}]
    if prev_conversation:
        for message in prev_conversation:
            messages.append(message)
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    print(system_prompt, user_prompt)
    print(response)
    if response.choices[0].message.content == "":
        print("Retrying LLM call")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature + 0.1
        )
        print(response)
    response_content = response.choices[0].message.content
    if not response_content:
        raise AssertionError("Received empty response from LLM.")
    return response_content


def eval_strategies(user, user_message):
    """
    Evaluate if user response mentions any strategies.
    """
    strategies = get_strategies(user.language_id)

    strategy_recogniser = AssistantAgent(
        name="Recognise_strategy",
        llm_config={"config_list": CONFIG_LIST},
        system_message=get_prompt(user, "sys_recognise_strategy").replace("${strategies}", str(strategies)),
    )
    strategy_formatter = AssistantAgent(
        name="Reformat_strategy",
        llm_config={"config_list": CONFIG_LIST},
        system_message=get_prompt(user, "sys_format_strategy"),
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
                "message": get_prompt(user, "format_strategy"),
                "max_turns": 1,
                "summary_method": "last_msg",
            },
        ]
    )
    print(chat_results)
    print("***********************")
    print(chat_results[0].summary)
    print(chat_results[1].summary)
    print(chat_results[-1].summary)
    regex = r"(\[\s*)({\s*\"index\":\s?[\d]+,\s*\"strategy\":\s?[\s\S]+(\s*},?)\s*)+(\s*\])"
    strategy_json = re.search(regex, chat_results[1].summary).group()
    return chat_results[0].summary, json.loads(strategy_json)


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

    context_eval = AssistantAgent(
        name="Evaluate_context",
        llm_config={"config_list": CONFIG_LIST},
        system_message=get_prompt(user, "sys_extract_strategy_for_frequency").replace("${strategies}", str(strategies)),
    )
    frequency_eval = AssistantAgent(
        name="Evaluate_frequency",
        llm_config={"config_list": CONFIG_LIST},
        system_message=get_prompt(user, "sys_format_frequency"),
    )

    initializer = UserProxyAgent(
        name="Init",
        code_execution_config=False
    )
    print(most_recent_response.message)
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
    regex = r"{\s*\"strategy\":\s?[\d]+,\s*\"frequency\":\s?[\d]\s*}"
    frequency_json = re.search(regex, chat_results[1].summary).group()
    print(frequency_json)
    return json.loads(frequency_json)


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
    contexts = get_contexts_content(user.language_id)
    strategies = get_strategies_content(user.language_id)
    prompt = get_prompt(user, "system").replace("${contexts}", str(contexts)).replace("${strategies}", str(strategies))
    return prompt


def get_start_prompt(context, user):
    prompt = get_prompt(user, "start")
    prompt = prompt.replace("${context}", str(context))
    return prompt


def get_frequency_prompt(user, context, strategy):
    prompt = get_prompt(user, "frequency")
    prompt = prompt.replace("${strategy}", str(strategy)).replace("${context}", context)
    return prompt


def get_complete_prompt(user, most_contexts_strat, const_strategy, avg_freq, total_strat, const_strategies):
    prompt = get_prompt(user, "interview_complete")
    prompt = prompt.replace("${most_contexts}", most_contexts_strat).replace("${const_strategy}",
                                                                             const_strategy).replace("${avg_freq}",
                                                                                                     str(avg_freq)).replace(
        "${total_strat}", str(total_strat)).replace("${const_strategies}", str(const_strategies))
    return prompt
