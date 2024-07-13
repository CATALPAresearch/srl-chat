import json
import os
import requests
from openai import OpenAI

HF_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
headers = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}
OLLAMA_API_URL = "http://132.176.10.80/api"
OLLAMA_HOST = "http://132.176.10.80"


def hf_query(payload):
    response = requests.post(HF_API_URL, headers=headers, json=payload)
    return response.json()


def get_hf_llm_message(prompt):
    output = hf_query({
        "inputs": prompt
    })
    generated_response = output[0]["generated_text"].split("[/INST]")[-1]
    return generated_response


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
        base_url=f"{OLLAMA_HOST}/v1",
        api_key="ollama",  # required, but unused
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
