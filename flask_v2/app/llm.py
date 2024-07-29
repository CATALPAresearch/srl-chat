import json
import os
import requests
from openai import OpenAI
from autogen import AssistantAgent, UserProxyAgent
from .db_utils.crud import get_strategies
import logging

OLLAMA_API_URL = "http://132.176.10.80/api"
OLLAMA_HOST = "http://132.176.10.80/v1"
OPENROUTER_HOST = "https://openrouter.ai/api/v1"
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

logger = logging.getLogger(__name__)


def get_llm_message(model, prompt, temperature):
    data = dict(model=model, prompt=prompt, stream=False, options={
        "temperature": temperature
    })
    response = requests.post(f"{OLLAMA_API_URL}/generate", data=json.dumps(data))
    print(response.content)
    response_json = json.loads(response.content.decode('utf8'))
    return response_json["response"]


def get_llm_response_openai(model, system_prompt, user_prompt, temperature):
    client = OpenAI(
        base_url=OPENROUTER_HOST,
        api_key=OPENROUTER_KEY
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            # {"role": "user", "content": "Who won the world series in 2020?"},
            # {"role": "assistant", "content": "The LA Dodgers won in 2020."},
            {"role": "user", "content": user_prompt}
        ],
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
            "model": "mistralai/codestral-mamba",
            "base_url": OPENROUTER_HOST,
            "api_key": OPENROUTER_KEY,
        }
    ]
    frequency_eval = AssistantAgent(
        name="Evaluate_frequency",
        llm_config={"config_list": config_list_code},
        system_message=f"""You are a JSON generator. Evaluate the user's answer. Determine whether the answer mentions a 
        number between 1 and 4 and reply with that number as the frequency number and the number of 
        the strategy from context in the following format: {{"strategy": <Index of strategy>, "frequency": <Frequency number>}}.
        """,
    )
    context_eval = AssistantAgent(
        name="Evaluate_context",
        llm_config={"config_list": config_list_read},
        system_message=f"""Extract strategy information. Give back the index of the strategy this message talks about 
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
