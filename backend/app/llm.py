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

    messages = [{"role": "system", "content": system_prompt}]
    if prev_conversation:
        messages.extend(prev_conversation)
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    send_user_feedback("Agent is working on your request...")

    attempts = 3
    timeout = 2  # seconds, for retry backoff
    response_content = ""

    while attempts > 0:
        try:
            response = get_response(client, messages, temperature, expected_fields_model, stream=stream)

            # Streaming mode: collect all tokens and return the full string
            if stream and hasattr(response, "__iter__"):
                for partial in response:
                    token_obj = getattr(partial, "message", None)
                    if token_obj:
                        token_text = getattr(token_obj, "content", str(token_obj))
                        response_content += token_text
                        send_user_feedback(token_text)  # Live feedback
                return response_content  # return accumulated text

            # Non-streaming mode
            response_message = getattr(response, "message", None)
            response_content = getattr(response_message, "content", None) if response_message else None

            if response_content:
                return response_content

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            attempts -= 1
            time.sleep(timeout)
            timeout *= 2  # exponential backoff

    raise AssertionError("Failed to get response from LLM after retries.")

def get_response(client, messages, temperature, expected_fields_model=None, stream=True):
    """
    Send request to LLM (Ollama or OpenAI) and return the response.
    If `stream=True`, response will be a generator yielding partial outputs.
    """
    response = None
    try:
        if evil:
            logger.info("Send request to OpenAI")
            response = client.chat(
                model=MODEL,
                messages=messages,
                temperature=temperature,
                stream=stream  # allow streaming
            )
        else:
            logger.info("Send request to Ollama")
            response = client.chat(
                model=MODEL,
                messages=messages,
                format=expected_fields_model.model_json_schema() if expected_fields_model else '',
                options={'temperature': temperature},
                stream=stream
            )
    except Exception as e:
        logger.error(f"call ollama client.chat failed: {e}")
        return None

    return response


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
