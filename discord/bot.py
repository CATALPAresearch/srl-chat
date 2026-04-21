"""Discord bot to talk to an LLM."""
from discord import Client, Intents, Interaction, Object, app_commands, DMChannel
import json
import requests
import os
import asyncio
import random
import time
from aiohttp import ClientSession
from dotenv import load_dotenv

load_dotenv()

MY_GUILD = Object(os.getenv('DISCORD_SERVER_ID'))  # development server

token = os.getenv('BOT_TOKEN')

CLIENT_NAME = "discord"
API_URL = os.getenv('API_URL', "http://127.0.0.1:5000")
session = None


async def start_conversation(language, userid):
    url = f"{API_URL}/startConversation"

    payload = json.dumps({
        "language": language,
        "client": CLIENT_NAME,
        "userid": userid
    })
    headers = {
        'Content-Type': 'application/json'
    }

    async with session.post(url, headers=headers, data=payload) as response:
        data = await response.text()  # or json()
        return data


async def reply(message, userid):
    url = f"{API_URL}/reply"

    payload = json.dumps({
        "message": message,
        "client": CLIENT_NAME,
        "userid": userid
    })
    headers = {
        'Content-Type': 'application/json'
    }
    async with session.post(url, headers=headers, data=payload) as response:
        data = await response.text()  # or json()
        return data


async def reset_conversation(user):
    print("Resetting conversation for user", user.id)
    url = f"{API_URL}/resetConversation"

    payload = json.dumps({
        "client": CLIENT_NAME,
        "userid": user.id
    })
    headers = {
        'Content-Type': 'application/json'
    }

    async with session.post(url, headers=headers, data=payload) as response:
        data = await response.text()  # or json()
        return data


async def send_delay_message(language, channel):
    update_messages = {
        "en": [
            "Please hold for a moment while I analyze your response.",
            "One moment, I am currently processing your input.",
            "I am reviewing your answer, please bear with me.",
            "Let me take a moment to reflect on that.",
            "I am reading your answer carefully, please give me a moment."
        ],
        "de": [
            "Bitte einen Moment Geduld, ich analysiere deine Antwort.",
            "Einen Augenblick, ich beschäftige mich gerade mit deiner Antwort.",
            "Ich bearbeite deine Eingabe, einen Moment bitte.",
            "Ich denke kurz darüber nach, einen kleinen Moment bitte.",
            "Ich lese mir deine Antwort gründlich durch, bitte hab kurz Geduld.",
        ]
    }
    message_after_seconds = 30
    timeout = 300
    start = time.time()
    try:
        while time.time() < start + timeout:
            await asyncio.sleep(message_after_seconds)
            response = random.choice(update_messages[language])
            message_after_seconds = 60
            await channel.send(response)
    except asyncio.CancelledError:
        raise


async def get_reply(message):
    headers = {'Content-Type': 'application/json; charset=utf-8', }
    lang_response = requests.get(f"{API_URL}/user_language?client={CLIENT_NAME}&userid={message.author.id}",
                                 headers=headers)
    user_language = lang_response.text
    task = asyncio.create_task(send_delay_message(user_language, message.channel))
    response = await reply(message.content, message.author.id)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Response received.")
    finally:
        return response


class MyClient(Client):
    def __init__(self, *, intents: Intents):
        super().__init__(command_prefix='!', intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self):
        global session
        session = ClientSession()
        print("Logged in as {0.user}".format(client))

    async def on_resumed(self):
        global session
        session = ClientSession()
        print("Resumed session as {0.user}".format(client))

    async def on_disconnect(self):
        await session.close()

    async def on_message(self, message):
        if (message.author == self.user or
                not isinstance(message.channel, DMChannel)):
            # Abort if the message was sent by this bot, or isn't in a DM channel
            return
        channel = message.channel
        async with channel.typing():
            if message.content == "!deleteall" and isinstance(message.channel, DMChannel):
                response = await reset_conversation(message.author)
            else:
                response = await get_reply(message)
        # Send response in chunks od 2000 characters or fewer to avoid Discord limit
        n = 2000
        chunks = [response[i:i+n] for i in range(0, len(response), n)]
        for chunk in chunks:
            await channel.send(chunk)


intents = Intents(messages=True)
client = MyClient(intents=intents)


async def talk_in_user_channel(user, language, translations):
    user_channel = await user.create_dm()
    await user_channel.send(translations['conversation_start'])

    async with user_channel.typing():
        message = await start_conversation(language, user.id)

    await user_channel.send(message)


@client.tree.command(name="InterviewAgent")
@app_commands.describe(
    language="'en' for English | 'de' für Deutsch",
)
async def interview_agent(interaction: Interaction, language: str):
    """Start a conversation with InterviewAgent!"""
    headers = {'Content-Type': 'application/json; charset=utf-8', }
    translations_response = requests.get(f"{API_URL}/translations/{language}",  headers=headers)
    try:
        translations_response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(translations_response.status_code, json.loads(translations_response.content))
        if translations_response.status_code == 400:
            await interaction.response.send_message(
                f"Hey {interaction.user.mention}! {json.loads(translations_response.content)}")
        return "Error: " + str(e)

    try:
        await interaction.response.send_message(
            f"Hey {interaction.user.mention}! {translations_response.json()['command_response']}")
        await talk_in_user_channel(interaction.user, language, translations_response.json())
    except Exception as e:
        print(e)
        await interaction.response.send_message("Sorry, something went wrong")


@client.tree.command(name='sync', description='Owner only')
async def sync(interaction: Interaction):
    if interaction.user.id == 565256380727164949:
        await client.tree.sync()
        await interaction.response.send_message('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')


client.run(token)
