import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
import json

load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")

if BOT_TOKEN is None:
    raise ValueError("TOKEN is not set. Please check your environment variables.")

def get_prefix(_, message):
    try:
        with open("data/prefixes.json", "r") as f:
            prefixes = json.load(f)
        return prefixes.get(str(message.guild.id), "!")
    except Exception:
        return "!"


intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    synced = await bot.tree.sync()
    print(f"✅ Synced {len(synced)} slash commands.")

async def main():
    async with bot:
        await bot.load_extension("cogs.prefix")
        await bot.load_extension("cogs.general")
        await bot.load_extension("cogs.moderation")
        await bot.load_extension("cogs.automod")
        await bot.load_extension("cogs.events")
        await bot.load_extension("cogs.muterole")
        await bot.load_extension("cogs.help_command")
       
asyncio.run(main())
bot.run(BOT_TOKEN)
