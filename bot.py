import discord
from discord.ext import commands
import json
import os

TOKEN = "MTM5MjQ1NTQ2NTU5MzQ3MTAxNw.GTxKTy.3-uyptW6_bEnL7UfZEQiA0iJd9NzWw_WOWFUq0"
DEFAULT_PREFIX = "!"

if os.path.exists("prefixes.json"):
    with open("prefixes.json", "r") as f:
        prefix_db = json.load(f)
else:
    prefix_db = {}

NO_PREFIX_USERS = [1105502119731150858]  # Replace with actual user IDs

def get_prefix(bot, message):
    guild_id = str(message.guild.id) if message.guild else None
    if message.author.id in NO_PREFIX_USERS:
        return commands.when_mentioned_or("", DEFAULT_PREFIX)(bot, message)
    return commands.when_mentioned_or(prefix_db.get(guild_id, DEFAULT_PREFIX))(bot, message)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

@bot.event
async def on_ready():
    print(f"Bot online as {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setprefix(ctx, new_prefix):
    prefix_db[str(ctx.guild.id)] = new_prefix
    with open("prefixes.json", "w") as f:
        json.dump(prefix_db, f, indent=2)
    await ctx.send(f"Prefix changed to `{new_prefix}`")

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)  
    await ctx.send(f"🏓 Pong! Latency: `{latency}ms`")

@bot.command(name="no_prefix")
async def no_prefix(ctx, action: str = None, member: discord.Member = None):
    if ctx.author.id != 1105502119731150858:
        return await ctx.send("❌ Only the bot owner can use this command.")

    if action not in ["add", "remove"] or member is None:
        return await ctx.send("Usage: `no_prefix add @user` or `no_prefix remove @user`")

    if action == "add":
        if member.id in NO_PREFIX_USERS:
            return await ctx.send(f"❌ {member.mention} already has no prefix.")
        NO_PREFIX_USERS.append(member.id)
        await ctx.send(f"✅ added no prefix to {member.mention}")

    elif action == "remove":
        if member.id not in NO_PREFIX_USERS:
            return await ctx.send(f"❌ {member.mention} is not in no prefix list.")
        NO_PREFIX_USERS.remove(member.id)
        await ctx.send(f"✅ removed no prefix from {member.mention}")


bot.run(TOKEN)

