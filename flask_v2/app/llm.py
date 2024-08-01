import json
import os
import re
import requests
from openai import OpenAI
from autogen import AssistantAgent, UserProxyAgent
from .db_utils.crud import get_strategies
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


def get_llm_response_openai(model, system_prompt, user_prompt, temperature, prev_conversation=[]):
    client = OpenAI(
        base_url=BASE_URL,
        api_key=API_KEY
    )

    messages = [{"role": "system", "content": system_prompt}]
    if prev_conversation:
        for message in prev_conversation:
            messages.append(message)
    messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    print(response)
    response_content = response.choices[0].message.content
    return response_content


def eval_strategies(user, user_message):
    """
    Evaluate if user response mentions any strategies.
    """
    strategies = get_strategies(user.language_id)

    strategy_recogniser = AssistantAgent(
        name="Recognise_strategy",
        llm_config={"config_list": CONFIG_LIST},
        system_message=f"""Read the user message and decide whether they have mentioned one or several strategies from 
        the following list: {strategies}, then state the strategy and its index in the list.""",
    )
    strategy_formatter = AssistantAgent(
        name="Reformat_strategy",
        llm_config={"config_list": CONFIG_LIST},
        system_message=f"""You generate JSON code. Respond with a valid JSON array only.""",
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
                "message": """
                Reformat the learning strategies to JSON. Output only an array of strategies, with each 
                strategy given in the format delimited by `````. Include no other content in your message. `````
                {{"index": <index as number>, "strategy": <name of strategy>}}.
                """,
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
    regex = r"\[[\s\S]*\]"
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
        system_message=f"""Extract strategy information. Give back the index of the strategy mentioned in the 
                message delimited by ###, based on the following list: {strategies}You are a number generator. 
                Do not suggest any code to execute. Respond with a single number only.""",
    )
    frequency_eval = AssistantAgent(
        name="Evaluate_frequency",
        llm_config={"config_list": CONFIG_LIST},
        system_message=f"""You generate JSON code. Respond with a valid JSON object only. Evaluate the user's message.
         Determine whether the answer mentions a number between 1 and 4 and reply with that number as the frequency 
         number and the number of the strategy from context in the following format: {{"strategy": <Index of strategy>,
         "frequency": <Frequency number>}}. Don't include any Python code to execute in your answer, just return JSON 
         output.""",
    )

    initializer = UserProxyAgent(
        name="Init",
        code_execution_config=False
    )
    chat_results = initializer.initiate_chats(
        [
            {
                "recipient": context_eval,
                "message": f"""{most_recent_response.message}""",
                "max_turns": 1,
                "summary_method": "last_msg",
            },
            {
                "recipient": frequency_eval,
                "message": f"""{user_message}""",
                "max_turns": 1,
                "summary_method": "last_msg",
            },
        ]
    )
    print(chat_results)
    print("***********************")
    print(chat_results[-1].summary)
    regex = r"{[\s\S]*}"
    frequency_json = re.search(regex, chat_results[1].summary).group()
    print(frequency_json)
    return json.loads(frequency_json)
