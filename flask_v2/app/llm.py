import json
import os
import requests

HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
headers = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}
OLLAMA_API_URL = "http://132.176.10.80/api"


def hf_query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


def get_hf_llm_message(prompt):
    output = hf_query({
        "inputs": prompt
    })
    generated_response = output[0]["generated_text"].split("[/INST]")[-1]
    return generated_response


def get_llm_message(model, prompt):
    data = dict(model=model, prompt=prompt, stream=False, options={
        "temperature": 1
    })
    response = requests.post(f"{OLLAMA_API_URL}/generate", data=json.dumps(data))
    print(response.content)
    response_json = json.loads(response.content.decode('utf8'))
    return response_json["response"]
