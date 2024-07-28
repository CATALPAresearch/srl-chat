"""Discord bot to talk to an LLM."""
from discord import Client, Intents, Interaction, Object, app_commands, DMChannel
import json
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from app.core import start_conversation, reply
from db_utils.crud import get_language

# MY_GUILD = Object(1237341194338570250)
MY_GUILD = Object(1243870532407922740)  # development server

token = os.environ['BOT_TOKEN']

CLIENT_NAME = "discord"


async def clear_messages(user, channel):
    print("Clearing bot messages from DM history")
    messages = [msg async for msg in channel.history(limit=200)]
    for msg in messages:
        if msg.author.id == user.id:
            print("deleting", msg)
            await msg.delete()


class MyClient(Client):
    language = ""

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
            response, status_code = reply(CLIENT_NAME, message.author.id, message.content)

        await channel.send(response)


intents = Intents(messages=True)
client = MyClient(intents=intents)


@client.tree.command(name="studybot")
@app_commands.describe(
    language="'en' for English | 'de' für Deutsch",
)
async def studybot(interaction: Interaction, language: str):
    """Start a conversation with StudyBot!"""
    with open("flask_v2/config/translations.json") as file:
        translations = json.load(file)

    if not get_language(language):
        await interaction.response.send_message(translations["language_not_supported_message"])
        return

    client.language = language

    await interaction.response.send_message(f"Hey {interaction.user.mention}! {translations[language]['command_response']}")
    user_channel = await interaction.user.create_dm()
    await user_channel.send(translations[language]['conversation_start'])

    async with user_channel.typing():
        message, status = start_conversation(language, CLIENT_NAME, interaction.user.id)

    await user_channel.send(message)


@client.tree.command(name='sync', description='Owner only')
async def sync(interaction: Interaction):
    if interaction.user.id == 565256380727164949:
        await client.tree.sync()
        await interaction.response.send_message('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')


client.run(token)
