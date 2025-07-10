import discord
import os

# Use your actual bot token directly here (for testing only)
TOKEN = "MTM5MjQ1NTQ2NTU5MzQ3MTAxNw.GrYOPT.67p4SLkWrqvrd5-00gDM7KgivUYjeEEpbr4TRI"  # Replace this!

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
