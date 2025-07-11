import discord
from discord.ext import commands
import json
import os

TOKEN = "MTM5MjQ1NTQ2NTU5MzQ3MTAxNw.GTxKTy.3-uyptW6_bEnL7UfZEQiA0iJd9NzWw_WOWFUq0"  # Replace with actual token
DEFAULT_PREFIX = "!"

if os.path.exists("prefixes.json"):
    with open("prefixes.json", "r") as f:
        prefix_db = json.load(f)
else:
    prefix_db = {}

NO_PREFIX_USERS = [1105502119731150858]  # Optional: load from file/database

def get_prefix(bot, message):
    if not message.guild:
        return DEFAULT_PREFIX

    guild_id = str(message.guild.id)
    custom_prefix = prefix_db.setdefault(guild_id, DEFAULT_PREFIX)

    # Save it back so it stays persistent
    with open("prefixes.json", "w") as f:
        json.dump(prefix_db, f, indent=2)

    if message.author.id in NO_PREFIX_USERS:
        return commands.when_mentioned_or("", custom_prefix)(bot, message)

    return commands.when_mentioned_or(custom_prefix)(bot, message)


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")
    print(f"🤖 Bot is online as {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def setprefix(ctx, new_prefix):
    guild_id = str(ctx.guild.id)
    prefix_db[guild_id] = new_prefix
    print(f"[DEBUG] Setting prefix for {guild_id} to {new_prefix}")
    
    try:
        with open("prefixes.json", "w") as f:
            json.dump(prefix_db, f, indent=2)
        await ctx.send(f"✅ Prefix changed to `{new_prefix}`")
        print("[DEBUG] prefixes.json updated successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to write prefixes.json: {e}")
        await ctx.send("❌ Failed to update prefix file.")


@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: `{latency}ms`")

@bot.tree.command(name="ping", description="Check bot latency")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latency: `{latency}ms`")

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

# DEBUG FORCE WRITE
with open("prefixes.json", "w") as f:
    json.dump({"test": "value"}, f)

bot.run(TOKEN)

