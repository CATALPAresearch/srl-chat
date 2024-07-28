"""Discord bot to talk to an LLM."""
from discord import Client, Intents, Interaction, Object, app_commands, DMChannel
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# MY_GUILD = Object(1237341194338570250)
MY_GUILD = Object(1243870532407922740)  # development server

token = os.getenv('BOT_TOKEN')

CLIENT_NAME = "discord"
API_URL = os.getenv('API_URL', "http://127.0.0.1:5000")


async def clear_messages(user, channel):
    print("Clearing bot messages from DM history")
    messages = [msg async for msg in channel.history(limit=200)]
    for msg in messages:
        if msg.author.id == user.id:
            print("deleting", msg)
            await msg.delete()


def start_conversation(language, userid):
    url = f"{API_URL}/startConversation"

    payload = json.dumps({
        "language": language,
        "client": CLIENT_NAME,
        "userid": userid
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.text


def reply(message, userid):
    url = f"{API_URL}/reply"

    payload = json.dumps({
        "message": message,
        "client": CLIENT_NAME,
        "userid": userid
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.text


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
        print("Logged in as {0.user}".format(client))

    # on message in user DM:
    # read user messages and surround with [INST] [/INST]
    # read system messages and append </s>
    # generate next response
    async def on_message(self, message):
        if (message.author == self.user or
                not isinstance(message.channel, DMChannel)):
            # Abort if the message was sent by this bot, or isn't in a DM channel
            return
        if message.content == "!clear" and isinstance(message.channel, DMChannel):
            await clear_messages(self.user, message.channel)
            return

        channel = message.channel
        async with channel.typing():
            response = reply(message.content, message.author.id)

        await channel.send(response)


intents = Intents(messages=True)
client = MyClient(intents=intents)


async def talk_in_user_channel(user, language, translations):
    user_channel = await user.create_dm()
    await user_channel.send(translations['conversation_start'])

    async with user_channel.typing():
        message = start_conversation(language, user.id)
        print(message)

    await user_channel.send(message)


@client.tree.command(name="studybot")
@app_commands.describe(
    language="'en' for English | 'de' für Deutsch",
)
async def studybot(interaction: Interaction, language: str):
    """Start a conversation with StudyBot!"""
    HEADERS = {'Content-Type': 'application/json; charset=utf-8', }
    translations_response = requests.get(f"{API_URL}/translations/{language}",  headers=HEADERS)
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
