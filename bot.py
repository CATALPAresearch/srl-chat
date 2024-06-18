"""Discord bot to talk to an LLM."""
from discord import Client, Intents, Interaction, Object, app_commands, DMChannel
import os
import requests

# MY_GUILD = Object(1237341194338570250)
MY_GUILD = Object(1243870532407922740)  # development server

translations = {
    "language_not_supported_message": """The language you have specified is currently not supported. Please specify 'en' for English or 'de' for German.
Die von dir gewünschte Sprache wird derzeit nicht unterstützt. Bitte gib entweder 'en' für Englisch oder 'de' für Deutsch an.""",
    "en": {
        "command_response": "Please check your DMs for a message from me.",
        "conversation_start": "Starting conversation...",
        "start_prompt": """[INST]You are a study advisor. Your task is to ask students to describe their study processes. Reply \
with a friendly greeting and a single question asking to describe their favourite study method.[/INST]"""
    },
    "de": {
        "command_response":  "Du bekommst gleich eine persönliche Nachricht von mir.",
        "conversation_start": "Unser Gespräch beginnt gleich...",
        "start_prompt": """[INST]Du bist ein Studienberater an einer deutschen Universität. Deine Aufgabe ist es, Studenten \
und Studentinnen nach ihren bevorzugten Lernmethoden zu fragen. Beginne das Gespräch mit einer \
freundlichen Begrüßung und einer Aufforderung, eine Lernmethode zu beschreiben, die die Person selbst \
oft einsetzt. Antworte stets auf Deutsch.[/INST]"""
    }
}


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
        if message.content == "!clear" and isinstance(message.channel, DMChannel):
            print("Clearing bot messages from DM history")
            channel = message.channel
            messages = [msg async for msg in channel.history(limit=200)]
            for msg in messages:
                if msg.author.id == self.user.id:
                    print("deleting", msg)
                    await msg.delete()
            return
        if (message.author == self.user or
                not isinstance(message.channel, DMChannel)):
            # Abort if the message was sent by this bot, or isn't in a DM channel
            return
        prompt = translations[client.language]["start_prompt"]
        channel = message.channel
        async with channel.typing():
            messages = [message async for message in channel.history(limit=200)]
            for message in reversed(messages):
                if message.author == self.user:
                    prompt += f"{message.content}</s>"
                else:
                    prompt += f"[INST]{message.content}[/INST]"
            next_message = get_llm_message(prompt)
        await channel.send(next_message)


intents = Intents(messages=True)
client = MyClient(intents=intents)

token = os.environ['BOT_TOKEN']

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
headers = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}


def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


def get_llm_message(prompt):
    output = query({
        "inputs": prompt
    })
    generated_response = output[0]["generated_text"].split("[/INST]")[-1]
    return generated_response


@client.tree.command(name="studybot")
@app_commands.describe(
    language="'en' for English | 'de' für Deutsch",
)
async def studybot(interaction: Interaction, language: str):
    """Start a conversation with StudyBot!"""
    if language != "en" and language != "de":
        await interaction.response.send_message(translations["language_not_supported_message"])
        return

    client.language = language

    await interaction.response.send_message(f"Hey {interaction.user.mention}! {translations[language]['command_response']}")
    user_channel = await interaction.user.create_dm()
    await user_channel.send(translations[language]['conversation_start'])
    async with user_channel.typing():
        llm_message = get_llm_message(translations[language]["start_prompt"])
    await user_channel.send(llm_message)


@client.tree.command(name='sync', description='Owner only')
async def sync(interaction: Interaction):
    if interaction.user.id == 565256380727164949:
        await client.tree.sync()
        await interaction.response.send_message('Command tree synced.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')


client.run(token)
