import json
import os
import requests
import time
import logging

from openai import OpenAI
from ollama import Client

from .database.crud import get_language_by_id, get_contexts_content, get_strategies_content

BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL = os.getenv("MODEL")
CONFIG_LIST = [
    {
        "model": MODEL,
        "base_url": BASE_URL,
        # "api_key": API_KEY,
    }
]
EMBEDDING_URL = os.getenv("EMBEDDING_URL", "https://huggingface.co/")
# https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_TOKEN = os.getenv("EMBEDDING_TOKEN", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
# https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2
logger = logging.getLogger('StudyBot')
evil = False
client = None


def query_embeddings(text_to_embed):
    api_url = f"{EMBEDDING_URL}{EMBEDDING_MODEL}"
    headers = {"Authorization": f"Bearer {EMBEDDING_TOKEN}"}
    response = requests.post(
        api_url,
        # headers=headers,
        json={"inputs": text_to_embed, "options": {"wait_for_model": True}})
    return response.json()


def get_model_names(base_url):
    """
    """
    client = Client(host=base_url)
    names = []
    for model in client.list()['models']:
        m = dict(model)
        names.append(m['model'])
    return names


_client_instance = None


def get_client():
    global _client_instance
    if _client_instance is None:
        if evil:
            _client_instance = OpenAI(base_url=BASE_URL)
        else:
            _client_instance = Client(
                host='http://localhost:11434',
                headers={'x-some-header': 'some-value'}
            )
    return _client_instance

def get_llm_response_openai(
        system_prompt,
        user_prompt=None,
        temperature=0.0,
        top_k=25,
        top_p=0.3,
        repeat_penalty=1.1,
        prev_conversation=[],
        expected_fields_model=None,
        stream=True
):
    # --- HARD DEV GUARD: skip LLM entirely ---
    if os.getenv("DISABLE_LLM", "false").lower() == "true":
        logger.warning("DISABLE_LLM=true - skipping LLM call")
        return (
            "Hallo! Lass uns mit dem Interview beginnen. "
            "In welchem Fach möchtest du einen Abschluss machen?"
        )

    logger.info("System Prompt: %s", system_prompt)
    logger.info("User Prompt: %s", user_prompt)

    global client
    if client is None:
        client = get_client()

        # Use user/assistant format instead of system role for llama3.2 compatibility
        messages = [
            {"role": "user", "content": system_prompt},
            {"role": "assistant", "content": "Understood, I will conduct the interview."},
        ]
        if prev_conversation:
            messages.extend(prev_conversation)
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        attempts = 5
        timeout = 0
        response = get_response(messages, temperature, expected_fields_model)
        while attempts > 0:
            if response is None or not hasattr(response, "message") or response.message.content == "":
                response = get_response(messages, temperature + 0.1, expected_fields_model)
                time.sleep(timeout)
                attempts -= 1
                timeout *= 2
            else:
                break

        logger.info('@llm: response::: ')
        logger.info(response)
        response_content = response.message.content if (response and hasattr(response, "message")) else None

        if not response_content:
            logger.info("Empty response")
            raise AssertionError("Received empty response from LLM.")
        logger.info("Response: %s", response_content)
        return response_content
def get_response(messages, temperature, expected_fields_model=None):
    """Call Ollama directly via HTTP REST API."""
    logger.info("Send request to Ollama via HTTP")
    try:
        payload = {
            "model": MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": 256,
                "num_ctx": 2048
            }
        }
        r = requests.post("http://localhost:11434/api/chat", json=payload, timeout=120)
        data = r.json()
        logger.info("Ollama raw response: %s", data)
        content = data.get("message", {}).get("content", "")
        mock = type('MockResponse', (), {'message': type('msg', (), {'content': content})()})()
        return mock
    except Exception as e:
        logger.error(f"HTTP call to Ollama failed: {e}")
        return None


def get_prompt(user, prompt_name):
    with open("config/prompts.json", "r", encoding="utf-8") as file:
        prompts = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    prompt = prompts[user_lang.lang_code][prompt_name]
    return prompt


def get_intro_prompt(user, limit):
    return get_prompt(user, "intro_check").replace("${limit}", str(limit))


def get_context_prompt(context, user):
    subject = user.study_subject
    prompt = get_prompt(user, "context")
    prompt = prompt.replace(
        "${context}", context).replace(
        "${subject}", subject)
    return prompt


def get_frequency_validate_prompt(user, strategy):
    prompt = get_prompt(user, "validate_frequency")
    prompt = prompt.replace("${strategy_for_frequency}", str(strategy))
    return prompt


def get_frequency_prompt(user, context, strategy):
    prompt = get_prompt(user, "frequency")
    prompt = prompt.replace("${strategy}", str(strategy)).replace("${context}", context)
    return prompt


def get_format_frequency_prompt(user, strategy, reasoning_response):
    prompt = get_prompt(user, "format_frequency")
    prompt = prompt.replace(
        "${strategy_for_frequency}", str(strategy)).replace(
        "${reasoning_response}", reasoning_response)
    return prompt


def get_strategy_analysis_prompt(user):
    from .config import get_interview_config_path
    with open(get_interview_config_path(), "r", encoding="utf-8") as file:
        interview_context = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    strat_info = []
    for category in interview_context[user_lang.lang_code]["categories"]:
        strat_info.append(category["strategies"])
    prompt = get_prompt(user, "recognise_strategy").replace("${strat_info}", str(strat_info))
    return prompt


def get_format_strategy_prompt(user, reasoning_response, conv_length, context, limit):
    from .config import get_interview_config_path
    with open(get_interview_config_path(), "r", encoding="utf-8") as file:
        interview_context = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    strat_info = []
    for category in interview_context[user_lang.lang_code]["categories"]:
        strat_info.append(category["strategies"])
    prompt = get_prompt(user, "format_strategy").replace(
        "${reasoning_response}", reasoning_response).replace(
        "${strat_info}", str(strat_info)).replace(
        "${len(prev_conversation)}", str(conv_length)).replace(
        "${context}", context).replace(
        "${limit}", str(limit))
    return prompt


def get_complete_prompt(user, most_contexts_strat, const_strategy, avg_freq, total_strat, const_strategies):
    prompt = get_prompt(user, "interview_complete")
    from .config import get_interview_config_path
    with open(get_interview_config_path(), "r", encoding="utf-8") as file:
        interview_context = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    strat_info = interview_context[user_lang.lang_code]["categories"]
    prompt = prompt.replace(
        "${most_contexts}", most_contexts_strat).replace(
        "${const_strategy}", const_strategy).replace(
        "${avg_freq}", str(avg_freq)).replace(
        "${total_strat}", str(total_strat)).replace(
        "${const_strategies}", str(const_strategies)).replace(
        "${strategies}", str(strat_info)
    )
    return prompt

def send_user_feedback(text):
    logger.info(f"[USER FEEDBACK] {text}")
