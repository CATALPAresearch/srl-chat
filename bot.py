"""Discord bot to talk to an LLM."""
from discord import Client, Intents, Interaction, Object, app_commands, DMChannel
import os
import requests

# MY_GUILD = Object(1237341194338570250)
MY_GUILD = Object(1243870532407922740)  # development server


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
        if message.content == "!clear" and isinstance(message.channel, DMChannel):
            print("Clearing bot messages from DM history")
            channel = message.channel
            messages = [msg async for msg in channel.history(limit=200)]
            for msg in messages:
                if msg.author.id == self.user.id:
                    print("deleting", msg)
                    await msg.delete()
        if (message.author == self.user or
                not isinstance(message.channel, DMChannel)):
            # Abort if the message was sent by this bot, or isn't in a DM channel
            return
        prompt = start_prompt
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

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
headers = {"Authorization": f"Bearer {os.environ['HF_TOKEN']}"}


def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()


start_prompt = """[INST]You are a study advisor. Your task is to ask students to describe their study processes. Reply 
               with a friendly greeting and a single question asking to describe their favourite study method.[/INST]"""
message_context = start_prompt


def get_llm_message(prompt):
    output = query({
        "inputs": prompt
    })
    generated_response = output[0]["generated_text"].split("[/INST]")[-1]
    return generated_response


@client.tree.command()
async def studybot(interaction: Interaction):
    """Start a conversation with StudyBot!"""
    await interaction.response.send_message(f'Hi, {interaction.user.mention}! ' +
                                            'Please check your DMs for a message from me.')
    user_channel = await interaction.user.create_dm()
    await user_channel.send(f'Starting conversation...')
    async with user_channel.typing():
        llm_message = get_llm_message(start_prompt)
    await user_channel.send(llm_message)


client.run(token)
