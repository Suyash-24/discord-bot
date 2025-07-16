import discord
from discord.ext import commands
import json
import os
from typing import Optional


PREFIX_FILE = "data/prefixes.json"
NOPREFIX_FILE = "data/noprefix.json"
DEFAULT_PREFIX = "!"

# Load prefix data
if os.path.exists(PREFIX_FILE):
    with open(PREFIX_FILE, "r") as f:
        prefix_db = json.load(f)
else:
    prefix_db = {}

# Load no-prefix data
if os.path.exists(NOPREFIX_FILE):
    with open(NOPREFIX_FILE, "r") as f:
        no_prefix_users = json.load(f)
else:
    no_prefix_users = []

def get_prefix(bot, message):
    if not message.guild:
        return DEFAULT_PREFIX
    guild_id = str(message.guild.id)
    prefix = prefix_db.get(guild_id, DEFAULT_PREFIX)

    if message.author.id in no_prefix_users:
        return commands.when_mentioned_or("", prefix)(bot, message)
    return commands.when_mentioned_or(prefix)(bot, message)

class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="setprefix")
    @commands.has_permissions(administrator=True)
    async def setprefix(self, ctx, prefix: str):
        guild_id = str(ctx.guild.id)
        prefix_db[guild_id] = prefix

        with open(PREFIX_FILE, "w") as f:
            json.dump(prefix_db, f, indent=2)

        await ctx.send(f"✅ Prefix set to `{prefix}`")

    @commands.command(name="no_prefix")
    async def no_prefix(self, ctx, action: Optional[str] = None, member: Optional[discord.Member] = None):

        if ctx.author.id != 1105502119731150858:  
            return await ctx.send("❌ Only the bot owner can use this.")

        if action not in ["add", "remove"] or not member:
            return await ctx.send("Usage: `no_prefix add @user` or `no_prefix remove @user`")

        if action == "add":
            if member.id in no_prefix_users:
                return await ctx.send("Already added.")
            no_prefix_users.append(member.id)
        else:
            if member.id not in no_prefix_users:
                return await ctx.send("Not in list.")
            no_prefix_users.remove(member.id)

        with open(NOPREFIX_FILE, "w") as f:
            json.dump(no_prefix_users, f, indent=2)

        await ctx.send(f"✅ {action}ed `{member}` to no-prefix list.")

async def setup(bot):
    bot.get_prefix = lambda message: get_prefix(bot, message)
    await bot.add_cog(Prefix(bot))
