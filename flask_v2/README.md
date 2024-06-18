## Overview

This app provides an API backend to hold a conversation with an AI agent capable of assessing 
self-regulated learning skills based on Zimmerman and Martinez-Pons' Self-Regulated Learning Interview Schedule.

Zimmerman, B. J., & Martinez-Pons, M. M. (1986). _Development of a Structured Interview for Assessing Student Use of Self-Regulated Learning Strategies._ American Educational Research Journal, 23(4), 614–628. https://doi.org/10.2307/1163093

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
|       | Populate learning contexts and strategies in database                                                                                                                                    |                                                    |
|       | Implement dialogue loop with chained LLM prompts to ask about strategies for each learning context in turn, evaluate answers' mention of strategies and ask required follow-up questions |
|       | Implement prediction of learner achievement and SRL skill based on interview responses                                                                                                   |
|       | Store results in database                                                                                                                                                                |
|       | Make answers and drawn conclusions viewable by users (including authentication; may be done after user testing has started)                                                              |