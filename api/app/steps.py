import re
import json

from .db_utils.crud import get_strategies
from .llm import get_llm_response_openai
from .models import User


def strategy_step(user: User, context: str, prev_conversation: list[str]):
    strategies = get_strategies(user.language_id)

    system_prompt = f"""Only answer in valid json format with the following fields:
        - 'strategies' (strategies the user already shared). If the answer does not mention a clearly identifiable 
        strategy, use the strategy name 'other'.
        - 'status', the only possible values:
            - 'completed' when the user has described at least one valid strategy
            - 'in_progress' if the user has not yet provided a clear strategy
        - 'comment' (your comment to the user).
    You are an interviewer conducting an interview that will be evaluated scientifically. 
    Your tone should be friendly but neutral. 
    Find out the user's learning strategies in the following context: {context}.
    Mark the step as complete when you can recognise one or more strategies from the following list 
    in their answer: {strategies}.
    If the answer does not mention a clearly identifiable strategy, ask the user to clarify."""

    json_output = try_get_json_completion(5, 0.0, 0.2, system_prompt, prev_conversation=prev_conversation,
                                          user_prompt=None)
    return json_output["strategies"], json_output["status"], json_output["comment"]


def frequency_step(user: User, prev_conversation: list[str]):
    strategy_for_frequency = user.conversation_state.strategy_for_frequency

    system_prompt = f"""Only answer in valid json format with the following fields:
    - strategy: {strategy_for_frequency}
    - frequency (the number that the user rated their use of the strategy as, 
    on a scale of 1 (rarely), 2 (sometimes), 3 (often), 4 (most of the time))
    - 'status', the only possible values:
        - 'in_progress' if the user has not yet provided a valid frequency rating
        - 'completed' when the Human (User) has provided a valid frequency rating
    - 'comment' (your comment to the Human).
    If the answer does not mention a valid frequency rating, ask the user to clarify.
    You are an interviewer conducting an interview that will be evaluated scientifically. 
    Your tone should be friendly but neutral. 
    """
    json_output = try_get_json_completion(5, 0.0, 0.2, system_prompt, prev_conversation=prev_conversation,
                                          user_prompt=None)
    return json_output["strategy"], json_output["frequency"], json_output["status"], json_output["comment"]


def probe_step(user: User, prev_conversation: list[str]):
    strategies = get_strategies(user.language_id)

    system_prompt = f"""Only answer in valid json format with the following fields:
        - 'strategies': one or more strategies from the following list that the user has mentioned in their answer: 
        {strategies}. If the answer does not mention a clearly identifiable strategy, use the strategy name 'other'.
        - 'status': 'completed' when the user has described at least one valid strategy
    """

    json_output = try_get_json_completion(5, 0.0, 0.2, system_prompt, prev_conversation=prev_conversation,
                                          user_prompt=None)
    return json_output["strategies"], json_output["status"]


def complete():
    pass


def format_strategy(user, message):
    strategies = get_strategies(user.language_id)
    system_prompt = f"""Only answer in valid json format. The output should be an array containing objects
                       with the following fields:
                            - 'index' (index as number),
                            - 'strategy' (name of strategy)
                       The only possible values are the indices and strategy names of this list: {strategies}"""
    json_output = try_get_json_completion(5, 0.0, 0.2, system_prompt, user_prompt=message)
    return json_output["index"]


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
            return json_output
        except AttributeError:
            attempts -= 1
            temperature += temp_increase
            continue
        else:
            break