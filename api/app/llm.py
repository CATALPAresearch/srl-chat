import json
import os
import requests
import time

from openai import OpenAI

from .db_utils.crud import get_language_by_id, get_contexts_content, get_strategies_content
import logging

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
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "https://api-inference.huggingface.co/pipeline/feature-extraction/")
EMBEDDING_TOKEN = os.getenv("EMBEDDING_TOKEN", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

logger = logging.getLogger(__name__)


def query_embeddings(text_to_embed):
    api_url = f"{EMBEDDING_URL}{EMBEDDING_MODEL}"
    headers = {"Authorization": f"Bearer {EMBEDDING_TOKEN}"}
    response = requests.post(api_url, headers=headers,
                             json={"inputs": text_to_embed, "options": {"wait_for_model": True}})
    return response.json()


def get_llm_response_openai(system_prompt, user_prompt=None, temperature=0.0, prev_conversation=[]):
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
        model=MODEL,
        messages=messages,
        temperature=temperature
    )
    # print(system_prompt, user_prompt)
    # print(response)
    attempts = 5
    timeout = 3
    while attempts > 0:
        if response.choices[0].message.content == "":
            print("Retrying LLM call")
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=temperature + 0.1
            )
            print(response)
            time.sleep(timeout)
            attempts -= 1
            timeout *= 2
        else:
            break
    response_content = response.choices[0].message.content
    if not response_content:
        raise AssertionError("Received empty response from LLM.")
    return response_content


def get_prompt(user, prompt_name):
    with open("app/config/prompts.json", "r", encoding="utf-8") as file:
        prompts = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    prompt = prompts[user_lang.lang_code][prompt_name]
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
