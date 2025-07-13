import discord
from discord.ext import commands
import json
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Load token from environment variable
DEFAULT_PREFIX = "!"


# Load no prefix users from file
def load_no_prefix_users():
    if os.path.exists("no_prefix_users.json"):
        with open("no_prefix_users.json", "r") as f:
            return json.load(f)
    return [1105502119731150858]  # Default owner ID

def save_no_prefix_users(data):
    with open("no_prefix_users.json", "w") as f:
        json.dump(data, f, indent=2)

NO_PREFIX_USERS = load_no_prefix_users()

# Load prefix database
def load_prefixes():
    if os.path.exists("prefixes.json"):
        with open("prefixes.json", "r") as f:
            return json.load(f)
    return {}

def save_prefixes(data):
    with open("prefixes.json", "w") as f:
        json.dump(data, f, indent=2)

prefix_db = load_prefixes()

def get_prefix(bot, message):
    guild_id = str(message.guild.id) if message.guild else None
    custom_prefix = prefix_db.get(guild_id, DEFAULT_PREFIX)

    # For users in NO_PREFIX_USERS, allow both prefix and no prefix
    if message.author.id in NO_PREFIX_USERS:
        return (custom_prefix, "", f"<@!{bot.user.id}> ", f"<@{bot.user.id}> ")
    return (custom_prefix, f"<@!{bot.user.id}> ", f"<@{bot.user.id}> ")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

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
    save_prefixes(prefix_db)
    await ctx.send(f"✅ Prefix changed to `{new_prefix}`")

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: `{latency}ms`")

@bot.tree.command(name="ping", description="Check bot latency")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! Latency: `{latency}ms`")

@bot.command(name="no_prefix")
async def no_prefix(ctx, action: str = "", member: str = ""):
    owner_id = NO_PREFIX_USERS[0] if NO_PREFIX_USERS else 1105502119731150858
    if ctx.author.id != owner_id:
        return await ctx.send("❌ Only the bot owner can use this command.")

    if action not in ["add", "remove"] or not member:
        return await ctx.send("Usage: `no_prefix add @user` or `no_prefix remove @user`")

    # Try to resolve member from mention or ID
    member_obj = None
    if member.isdigit():
        member_obj = ctx.guild.get_member(int(member))
    else:
        if member.startswith("<@") and member.endswith(">"):
            member_id = member.replace("<@","").replace(">","").replace("!","")
            if member_id.isdigit():
                member_obj = ctx.guild.get_member(int(member_id))
    if not member_obj:
        return await ctx.send("❌ Could not find that member in this server.")

    if action == "add":
        if member_obj.id in NO_PREFIX_USERS:
            return await ctx.send(f"❌ {member_obj.mention} already has no prefix.")
        NO_PREFIX_USERS.append(member_obj.id)
        save_no_prefix_users(NO_PREFIX_USERS)
        await ctx.send(f"✅ Added no prefix for {member_obj.mention}")

    elif action == "remove":
        if member_obj.id not in NO_PREFIX_USERS:
            return await ctx.send(f"❌ {member_obj.mention} is not in the no prefix list.")
        NO_PREFIX_USERS.remove(member_obj.id)
        save_no_prefix_users(NO_PREFIX_USERS)
        await ctx.send(f"✅ Removed no prefix from {member_obj.mention}")

if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN environment variable not set.")
bot.run(TOKEN)