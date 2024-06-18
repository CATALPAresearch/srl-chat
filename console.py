"""Console app to talk to an LLM."""
import os
import requests


token = os.environ['BOT_TOKEN']

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
headers = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}


def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


start_prompt = """[INST]You are a study advisor. Your task is to ask students to describe their study processes. Reply 
               with a friendly greeting and a single question asking to describe their favourite study method.[/INST]"""
message_context = start_prompt


def get_llm_message(prompt):
    output = query({
        "inputs": prompt
    })
    generated_response = output[0]["generated_text"].split("[/INST]")[-1]
    updated_prompt = prompt + generated_response + "</s>"
    return generated_response, updated_prompt


llm_message, message_context = get_llm_message(start_prompt)
print(llm_message)


while True:
    user_reply = input()
    message_context += f"[INST]{user_reply}[/INST]"
    llm_response, message_context = get_llm_message(message_context)
    print(llm_response)


