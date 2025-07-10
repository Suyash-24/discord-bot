import discord
from discord.ext import commands
from discord import app_commands

TOKEN = "MTM5MjQ1NTQ2NTU5MzQ3MTAxNw.GTxKTy.3-uyptW6_bEnL7UfZEQiA0iJd9NzWw_WOWFUq0"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Slash command sync failed: {e}")
    print(f"Bot is online as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! (from !ping)")

@bot.tree.command(name="ping", description="Replies with Pong!")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong! (from /ping)")

bot.run(TOKEN)
