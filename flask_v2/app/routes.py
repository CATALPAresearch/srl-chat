from json import JSONDecodeError

from app import app, db
from app.models import User, Language

from flask import request
import json
import sqlalchemy as sa
from xml.sax.saxutils import escape as xmlescape
from html import escape as htmlescape
from autogen import AssistantAgent, ConversableAgent, GroupChat, GroupChatManager, UserProxyAgent

from app.llm import get_llm_message
from db_utils.crud import (
    get_language,
    get_language_by_id,
    get_user,
    first_time_setup,
    get_strategies,
    get_contexts,
    get_context_by_id,
    store_answer,
    set_current_context,
    set_context_completed,
    get_completed_contexts,
    update_most_recent_response,
    update_answer_with_frequency
)


@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"


@app.route('/user/<id>')
def get_user_by_id(id):
    user = db.session.scalar(
        sa.select(User).where(User.id == id))
    if user is None:
        return "User not found", 404
    return user.client


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

    llm_message = get_llm_message("mixtral", start_prompt, 0.8)

    return llm_message


@app.route("/autogen_test", methods=['POST'])
def autogen():
    config_list = [
        {
            "model": "mixtral",
            "base_url": "http://132.176.10.80/v1",
            "api_key": "ollama",
        }
    ]
    content = request.json
    user_message = content["message"]
    agent = ConversableAgent(
        "chatbot",
        llm_config={"config_list": config_list},
        code_execution_config=False,  # Turn off code execution, by default it is off.
        function_map=None,  # No registered functions, by default it is None.
        human_input_mode="NEVER",  # Never ask for human input.
    )
    response = agent.generate_reply(messages=[{"content": user_message, "role": "user"}])
    return response

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

    return eval_strategies(user, user_message)

    match user.conversation_state.most_recent_response:
        case "getstrategies":
            identified_strategy = eval_strategies(user, user_message)
            # Identify ID of "other" strategy (corresponding to no concrete strategy mentioned)
            # no_strategy_mentioned = list(filter(lambda strategy: strategy[1] == "other", strategies))
            # Store user's answer
            store_answer(user, current_context_id, identified_strategy["index"], user_message)

            if identified_strategy["strategy"] == "other":
                # Probe further if "other" strategy identified

                probe_prompt = get_probe_prompt(current_context.context, user)
                update_most_recent_response(user, "probe")
                llm_message = get_llm_message("mixtral", probe_prompt, 0.9)
            else:
                frequency_prompt = get_frequency_prompt(user, current_context.context, identified_strategy)
                update_most_recent_response(user, "frequency")
                llm_message = get_llm_message("mixtral", frequency_prompt, 0.9)

        case "probe":
            identified_strategy = eval_strategies(user, user_message)
            store_answer(user, current_context_id, identified_strategy, user_message)
            if identified_strategy["strategy"] == "other":
                next_context = set_current_context_complete(user, current_context_id)
                context_prompt = get_context_prompt(next_context.context, user)
                update_most_recent_response(user, "getstrategies")
                llm_message = get_llm_message("mixtral", context_prompt, 0.9)
            else:
                frequency_prompt = get_frequency_prompt(user, current_context.context, identified_strategy)
                update_most_recent_response(user, "frequency")
                llm_message = get_llm_message("mixtral", frequency_prompt, 0.9)

        case "frequency":
            eval_frequency_prompt = get_eval_frequency_prompt(user, user_message)
            llm_eval = get_llm_message("mixtral", eval_frequency_prompt, 1)
            update_answer_with_frequency(user, current_context_id, llm_eval)

            next_context = set_current_context_complete(user, current_context_id)
            context_prompt = get_context_prompt(next_context.context, user)
            update_most_recent_response(user, "getstrategies")
            llm_message = get_llm_message("mixtral", context_prompt, 0.9)

        case _:
            pass

    return llm_message


def eval_strategies(user, user_message):
    """
    Evaluate if user response mentions any strategies.
    """
    strategies = get_strategies(user.language_id)
    config_list_read = [
        {
            "model": "mixtral",
            "base_url": "http://132.176.10.80/v1",
            "api_key": "ollama",
        }
    ]
    config_list_code = [
        {
            "model": "openhermes2.5-mistral",
            "base_url": "http://132.176.10.80/v1",
            "api_key": "ollama",
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
        the following information: {strategies}. Output an array of strategies with each strategy given in the 
        following format: {{"index": <index as number>, "strategy": <name of strategy>}}""",
    )

    def state_transition(last_speaker, group_chat):
        messages = group_chat.messages

        if last_speaker is strategy_recogniser:
            return strategy_formatter
        elif last_speaker is strategy_formatter:
            try:
                json.loads(messages[-1]["content"])
                return None
            except JSONDecodeError:
                # retrieve --(execution failed)--> retrieve
                return strategy_formatter

    group_chat = GroupChat(
        agents=[strategy_recogniser, strategy_formatter],
        messages=[],
        max_round=3,
        speaker_selection_method=state_transition,
    )
    manager = GroupChatManager(groupchat=group_chat, llm_config={"config_list": config_list_read})
    initializer = UserProxyAgent(
        name="Init",
        code_execution_config=False
    )
    # chat = initializer.initiate_chat(
    #     manager,
    #     message=user_message
    # )
    chat = strategy_recogniser.initiate_chat(
        strategy_formatter,
        message=user_message,
        max_turns=2
    )
    print(chat)
    return chat.summary

    # prompt = get_eval_prompt(strategies, user_message, user)
    # llm_eval = get_llm_message("mixtral", prompt, 1)
    # identified_strategy = json.loads(llm_eval)[0]
    # return identified_strategy


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

    llm_message = get_llm_message("mixtral", start_prompt, 0.8)

    return llm_message
