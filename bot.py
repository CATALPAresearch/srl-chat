from discord import Client, Intents, Interaction, Object, app_commands
import os
import requests

MY_GUILD = Object(1237341194338570250)


class MyClient(Client):
    def __init__(self, *, intents: Intents):
        super().__init__(intents=intents)
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


intents = Intents(messages=True)
client = MyClient(intents=intents)

token = os.environ['BOT_TOKEN']

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
headers = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}


def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


def get_first_llm_message():
    output = query({
        "inputs": """<s>[INST]You are a study advisor. Your task is to ask students to describe their study processes. Reply 
               with a friendly greeting and a single question asking to describe their favourite study method.[/INST]""",
    })
    return output[0]["generated_text"].split("[/INST]")[1]


@client.tree.command()
async def studybot(interaction: Interaction):
    """Start a conversation with StudyBot!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}! ' +
                                            'Please check your DMs for a message from me.')
    user_channel = await interaction.user.create_dm()
    await user_channel.send(f'Starting conversation...')
    async with user_channel.typing():
        llm_message = get_first_llm_message()
    await user_channel.send(llm_message)


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))


client.run(token)
