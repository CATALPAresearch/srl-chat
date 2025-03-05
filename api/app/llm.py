import json
import os
import requests
import time
import logging

from openai import OpenAI
from ollama import Client
from ollama import chat
from ollama import ChatResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama

from .db_utils.crud import get_language_by_id, get_contexts_content, get_strategies_content

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
#https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_TOKEN = os.getenv("EMBEDDING_TOKEN", "")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
#https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2
logger = logging.getLogger('StudyBot')
evil = False

def query_embeddings(text_to_embed):
    api_url = f"{EMBEDDING_URL}{EMBEDDING_MODEL}"
    headers = {"Authorization": f"Bearer {EMBEDDING_TOKEN}"}
    response = requests.post(
        api_url, 
        #headers=headers,
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


def get_llm_response_openai(system_prompt, user_prompt=None, temperature=0.0, top_k=25, top_p=0.3, repeat_penalty=1.1, prev_conversation=[]):
    logger.info("Generation prompt: %s", system_prompt)
    
    if evil:
        client = OpenAI(
            base_url=BASE_URL,
            #api_key=API_KEY
        )
    else:
        """
        client = ChatOllama(
            model=MODEL, 
            base_url=BASE_URL,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repeat_penalty=repeat_penalty,
        )
        """
        client = Client(
            host='http://localhost:11434',
            headers={'x-some-header': 'some-value'} #FixMe
            )

    messages = [{"role": "system", "content": system_prompt}]
    if prev_conversation:
        for message in prev_conversation:
            messages.append(message)
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})
    logger.info("User Message: %s", messages[-1])
    logger.info('----xx-----')
    response = get_response(client, messages, temperature)

    logger.info("First response: %s", response['message']['content'])
    attempts = 5
    timeout = 3
    #return response['message']['content']
    while attempts > 0:
        if response.message.content == "":
            logger.info("Retrying LLM call for prompt: %s\nUser Message: %s", system_prompt, messages[-1])
            response = get_response(client, messages, temperature+0.1)
            logger.info(str(attempts)+". - response: %s", response['message']['content'])
            time.sleep(timeout)
            attempts -= 1
            timeout *= 2
        else:
            break
    ##response_content = response.choices[0].message.content
    response_content = response.message.content
    if not response_content:
        logger.info("Empty response")
        raise AssertionError("Received empty response from LLM.")
    logger.info("Response: %s", response_content)
    return response_content



def get_response(client, messages, temperature):
    response = ''
    if evil: 
        logger.info("Send request to openAI")
        response = client.chat.completion.create(
            model=MODEL,
            messages=messages,
            temperature=temperature
        )
    else:
        logger.info('............')
        logger.info("Send request to Ollama")
        logger.info(messages[-1]['role'])
        logger.info('............')
        response = client.chat(
            #model='llama3.1:latest', 
            model=MODEL, 
            #messages=messages, 
            messages=[
            {
                'role': messages[-1]['role'],
                'content': messages[-1]['content'], #"You are an interviewer conducting an interview that will be evaluated scientifically. Your tone should be friendly but neutral. Refer back to the user's answers, but do not comment positively or negatively on them. You are guiding a student through an interview to assess their study skills. Start the conversation with a friendly greeting. Ask the student which subject the degree they are studying is about.",
            }],
            stream=False
            )
    return response


def get_prompt(user, prompt_name):
    with open("app/config/prompts.json", "r", encoding="utf-8") as file:
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
    with open("app/config/interview.json", "r", encoding="utf-8") as file:
        interview_context = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    strat_info = []
    for category in interview_context[user_lang.lang_code]["categories"]:
        strat_info.append(category["strategies"])
    prompt = get_prompt(user, "recognise_strategy").replace("${strat_info}", str(strat_info))
    return prompt


def get_format_strategy_prompt(user, reasoning_response, conv_length, context, limit):
    with open("app/config/interview.json", "r", encoding="utf-8") as file:
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
    with open("app/config/interview.json", "r", encoding="utf-8") as file:
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
