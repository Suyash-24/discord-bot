import os
from dotenv import load_dotenv
import discord

  # Loads from .env file locally

TOKEN = os.getenv("BOT_TOKEN")  # Grabs token from env var

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")

client.run(TOKEN)
