## Overview

This app provides an API backend to hold a conversation with an AI agent capable of assessing 
self-regulated learning skills based on Zimmerman and Martinez-Pons' Self-Regulated Learning Interview Schedule.

Zimmerman, B. J., & Martinez-Pons, M. M. (1986). _Development of a Structured Interview for Assessing Student Use of Self-Regulated Learning Strategies._ American Educational Research Journal, 23(4), 614–628. https://doi.org/10.2307/1163093

## Local development

The API and Discord bot can be started using Docker Compose. For local development, the API container's port 5000 is exposed while for deployment, for security reasons, the API is not exposed to the internet but only accessible from other containers within the Compose network.
The Compose file starts the API server in development mode so that it automatically reloads when any changes are made to files in the `api` directory. Note that the Discord bot needs to be restarted manually after changes are made.

**Prerequisit: Postgresql**
First, a current version of Postgresql should be installed, e.g. on MacOS
''''
brew install postgresql@17
brew link --overwrite postgresql@17
'''
Check if postgresql is running smoothly: 'brew services info postgresql@17'

Second, the vector extension is required for postgres.
"""
brew install pgvector
brew services start postgresql@17 && sleep 1
"""
Activate pgvector: 'psql -d postgres -c 'CREATE EXTENSION vector'

**Install SRL Chat**
- Clone the git repository
- Copy the env.example file, renaming the new file .env inside xxxx
- Set BASE_URL=https://chat-impact.fernuni-hagen.de/ollama/v1 to use the university hosted Ollama server, or to the URL of any other OpenAPI compatible endpoint
- OPTIONAL (currently disabled): Set API_KEY to the required API key (Bearer token starting with sk-...) for the BASE_URL. If no API key is required, this field must still be set to any dummy value

**Test the setup**
Test whether your Ollama is working, e.g.
'''
curl http://localhost:11434/api/generate -d '{"model": "llama3.1:latest", "prompt": "Why is the sky blue?"}'
'''

Test whether the agents starts a conversation:
'''
curl -X POST http://localhost:5000/startConversation -H "Content-Type: application/json" -d '{ "language": "en", "client": "discord", "userid": "123456789"}'
'''

### Running the app locally

Prerequisites: A system with Docker and Docker Compose installed.

- Clone the git repository
- Copy the env.example file, renaming the new file .env
- Set BASE_URL=https://chat-impact.fernuni-hagen.de/ollama/v1 to use the university hosted Ollama server, or to the URL of any other OpenAPI compatible endpoint
- Set API_KEY to the required API key (Bearer token starting with sk-...) for the BASE_URL. If no API key is required, this field must still be set to any dummy value
- Set PG_HOST=localhost
- Set MODEL to one that is available under the BASE_URL instance (for example meta-llama/llama-3.1-8b-instruct or mistralai/mixtral-8x22b-instruct)
- The other settings can stay as they are. There should be no need to set BOT_TOKEN, API_URL or DISCORD_SERVER_ID as these are required for the Discord bot which is not required for local testing
- Run the following command:
```shell
docker compose -f develop.docker-compose.yml up postgres-dev api-dev
```



---
docker compose build --no-cache
docker compose up -d
----

###
'poetry init'
'for item in $(cat requirements.txt); do poetry add "${item}"; done'
'poetry update'
'poetry run boty.py'

The following endpoints will then be available:

```http request
POST http://127.0.0.1:5000/startConversation
Content-Type: application/json

{
    "language": "de", // "de" or "en" currently supported
    "client": "discord",
    "userid": "123" // needs to be unique for the client, can be set to any string value when testing locally
}
```

```http request
POST http://127.0.0.1:5000/reply
Content-Type: application/json

{
    "message": "A user response",
    "client": "discord",
    "userid": "123" // client and user values need to match the values sent in startConversation request
}
```

#### Local App Testing

1. To start the conversation, send an HTTP request to the `/startConversation` endpoint, providing language, client name and user ID in the request body as shown. An API testing tool like [Postman](https://www.postman.com/downloads/) can be used for this purpose.
2. The response from the endpoint represents the response from the Conversational Agent.
3. To reply, send an HTTP request to the `/reply` endpoint. Set the `message` field in the request body to the user response and ensure to keep the values of `client` and `userid` equal to those that the conversation was started with.
4. The response from the endpoint represents the response from the Conversational Agent. To exchange further messages, continue using the `/reply` endpoint providing the same `client` and `userid`.
5. To reset the conversation, archive all data and restart the conversation from the `/startConversation` endpoint, send `!deleteall` as the content of the user message.