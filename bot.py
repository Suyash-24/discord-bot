import discord
import os

# Use your actual bot token directly here (for testing only)
TOKEN = "MTM5MjQ1NTQ2NTU5MzQ3MTAxNw.GTxKTy.3-uyptW6_bEnL7UfZEQiA0iJd9NzWw_WOWFUq0"  # Replace this!

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content == "ping":
        await message.channel.send("pong")

client.run(TOKEN)
