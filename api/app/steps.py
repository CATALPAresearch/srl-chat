import re
import json

from .db_utils.crud import get_language_by_id, get_all_strategies, retrieve_similar_docs_vector
from .llm import get_llm_response_openai, query_embeddings
from .models import User


def strategy_step(user: User, context: str, prev_conversation: list[str], user_message):
    user_answer_embedding = query_embeddings(user_message)
    related_docs = retrieve_similar_docs_vector(user_answer_embedding)
    strategy_candidates = []
    for doc in related_docs:
        strategy_candidates.append({"id": doc.strategy, "description": doc.description})
    print(strategy_candidates)

    system_prompt = f"""Analyse the user's answer and decide if they are describing one of the strategies in this list:
    {str(strategy_candidates)}. Explain which one and why. If you cannot recognise a clear strategy from their answer,
    explain why and state what additional information would be required to decide if they are using one of the strategies.
    State 'complete' at the end of your message if you have enough information to categorise the strategy and 'in_progress' if not."""
    llm_message = get_llm_response_openai(system_prompt, user_prompt=None, temperature=0.0,
                                          prev_conversation=prev_conversation)
    print("RAG:", llm_message)

    with open("app/config/interview.json", "r", encoding="utf-8") as file:
        interview_context = json.load(file)
    user_lang = get_language_by_id(user.language_id)
    strat_info = []
    for category in interview_context[user_lang.lang_code]["categories"]:
        strat_info.append(category["strategies"])

    system_prompt = f"""Analyse the user's answer and decide if they are describing one of the strategies in this list:
        {str(strat_info)}. Explain which one and why. If you cannot recognise a clear strategy from their answer,
        explain why and state what additional information would be required to decide if they are using one of the strategies.
        State 'complete' at the end of your message if you have enough information to categorise the strategy and 'in_progress' if not."""
    llm_message = get_llm_response_openai(system_prompt, user_prompt=None, temperature=0.0,
                                          prev_conversation=prev_conversation)
    print("LIST:", llm_message)

    system_prompt = f"""Only answer in valid json format with the following fields:
        - 'strategies' (IDs of the strategies the user already shared in the conversation).
        - 'status', the possible values:
            - 'completed' if the user has described at least one valid strategy. Mark the step as complete when you 
            can recognise one or more strategies from the following list in their answer: {strat_info}.
            - 'in_progress' if the user has given an invalid answer or their answer does not match any of the strategies in the list.
            Ask the user to clarify, but do not include any suggestions or examples of strategies in your answer.
            - 'abandon', if the user has not described a clearly identifiable strategy after 10 exchanged messages.
            Number of exchanged messages so far: {len(prev_conversation)}
        - 'comment' (your comment to the user. Do not include any suggestions or examples of strategies).
    You are an interviewer conducting an interview that will be evaluated scientifically. 
    Your tone should be friendly but neutral. 
    Find out the user's learning strategies in the following context: {context}."""

    json_output, json_valid = try_get_json_completion(5, 0.0, 0.2, system_prompt, prev_conversation=prev_conversation,
                                                      user_prompt=None)
    if not json_valid:
        return [], "in_progress", json_output
    if json_output["strategies"] in ([], ["other"]) and len(prev_conversation) >= 10:
        json_output["strategies"] = ["other"]
        json_output["status"] = "abandon"
    return json_output["strategies"], json_output["status"], json_output["comment"]


def frequency_step(user: User, prev_conversation: list[str]):
    strategy_for_frequency = user.conversation_state.strategy_for_frequency

    system_prompt = f"""Only answer in valid json format with the following fields:
    - strategy: {strategy_for_frequency}
    - frequency (the number that the user rated their use of the strategy as, 
    on a scale of 1 (rarely), 2 (sometimes), 3 (often), 4 (most of the time))
    - 'status', the only possible values:
        - 'in_progress' if the user has not yet provided a valid frequency rating
        - 'completed' when the user has provided a valid frequency rating
        - 'abandon', if the user has not provided a valid frequency rating after 10 exchanged messages
    - 'comment' (your comment to the Human).
    If the answer does not mention a valid frequency rating, ask the user to clarify.
    You are an interviewer conducting an interview that will be evaluated scientifically. 
    Your tone should be friendly but neutral. 
    """
    json_output, json_valid = try_get_json_completion(5, 0.0, 0.2, system_prompt, prev_conversation=prev_conversation,
                                                      user_prompt=None)
    if not json_valid:
        return [], 0, "in_progress", json_output
    if json_output["status"] == "in_progress" and len(prev_conversation) > 10:
        json_output["status"] = "abandon"
        json_output["frequency"] = 0
    return json_output["strategy"], json_output["frequency"], json_output["status"], json_output["comment"]


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
        num_attempts, start_temp, temp_increase, system_prompt, prev_conversation=[], user_prompt=None
):
    attempts = num_attempts
    temperature = start_temp
    while attempts > 0:
        try:
            llm_message = get_llm_response_openai(system_prompt, user_prompt=user_prompt, temperature=temperature,
                                                  prev_conversation=prev_conversation)
            print("RESP:", llm_message)
            regex = r"{[\s\S]+}"
            json_string = re.search(regex, llm_message).group()
            json_output = json.loads(json_string)
            print("JSON:", json_output)
            json_valid = True
            return json_output, json_valid
        except AttributeError:
            attempts -= 1
            temperature += temp_increase
            continue

    json_valid = False
    return llm_message, json_valid
