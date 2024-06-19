## Overview

This app provides an API backend to hold a conversation with an AI agent capable of assessing 
self-regulated learning skills based on Zimmerman and Martinez-Pons' Self-Regulated Learning Interview Schedule.

Zimmerman, B. J., & Martinez-Pons, M. M. (1986). _Development of a Structured Interview for Assessing Student Use of Self-Regulated Learning Strategies._ American Educational Research Journal, 23(4), 614–628. https://doi.org/10.2307/1163093

## Running the app locally

```shell
cd .\flask_v2\
flask run # use --reload option to interactively restart the app following code changes
```

The following endpoints will then be available:

```http request
POST http://127.0.0.1:5000/startConversation
Content-Type: application/json

{
    "language": "de", // "de" or "en" currently supported
    "client": "discord",
    "userid": "123" // needs to be unique for the client
}
```

```http request
POST http://127.0.0.1:5000/reply
Content-Type: application/json

{
    "message": "A user response",
    "client": "discord",
    "userid": "56"
}
```

## Making changes to the DB

```shell
cd .\flask_v2\
flask db migrate -m "Describe migration"
flask db upgrade
```

### To reinitialise DB from scratch

- Delete *.db file

```shell
flask db upgrade
python

Python 3.12.3 (tags/v3.12.3:f6650f9, Apr  9 2024, 14:05:25) [MSC v.1938 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> from setup.db_setup import populate_contexts
>>> populate_contexts()

```

## App Structure

![system_arch.png](..%2Fsystem_arch.png)

## Dialogue Flow

![interview.png](..%2Finterview.png)

## Current status

The following steps need to be completed before the app is ready for user testing:

| Done? | Task                                                                                                                                                                                     |
|-------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ✓     | Define database models required for the app to function: users, conversation state and supported languages                                                                               |                                                                                                           |
| ✓     | Define database models for required interview elements: learning contexts, learning strategies and user answers connecting them                                                          |
| ✓     | Create API endpoint to send first response and perform initial setup for users in database                                                                                               |
| ✓     | Create API endpoint to reply to user message based on previous messages                                                                                                                  |
| ✓     | Populate learning contexts and strategies in database                                                                                                                                    |                                                    |
|       | Implement dialogue loop with chained LLM prompts to ask about strategies for each learning context in turn, evaluate answers' mention of strategies and ask required follow-up questions |
|       | Implement prediction of learner achievement and SRL skill based on interview responses                                                                                                   |
|       | Store results in database                                                                                                                                                                |
|       | Make answers and drawn conclusions viewable by users (including authentication; may be done after user testing has started)                                                              |