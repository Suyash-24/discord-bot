
import discord
from discord.ext import commands
import json
import os
import typing



PREFIX_FILE = "data/prefixes.json"
NOPREFIX_FILE = "data/noprefix.json"
DEFAULT_PREFIX = "!"

try:
    with open(PREFIX_FILE, "r") as f:
        prefix_db = json.load(f)
except Exception:
    prefix_db = {}

try:
    with open(NOPREFIX_FILE, "r") as f:
        no_prefix_users = json.load(f)
except Exception:
    no_prefix_users = []


def get_prefix(bot, message):
    if not message.guild:
        return DEFAULT_PREFIX
    guild_id = str(message.guild.id)
    prefix = prefix_db.get(guild_id, DEFAULT_PREFIX)
    if message.author.id in no_prefix_users:
        return ("")
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

        embed = discord.Embed(
            title="✅ Prefix Set",
            description=f"Prefix set to `{prefix}`.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command(name="no_prefix")
    async def no_prefix(self, ctx, action: typing.Optional[str] = None, member: typing.Optional[typing.Union[discord.Member, str, int]] = None):
        if ctx.author.id != 1105502119731150858:
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="Only the bot owner can use this.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await ctx.send(embed=embed)
            return

        resolved = None
        if member is not None:
            if isinstance(member, discord.Member):
                resolved = member
            else:
                try:
                    member_id = int(member)
                    resolved = ctx.guild.get_member(member_id)
                except Exception:
                    pass

        if action not in ["add", "remove"] or not resolved:
            embed = discord.Embed(
                title="ℹ️ Usage",
                description="Usage: `no_prefix add @user` or `no_prefix remove @user`",
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow()
            )
            await ctx.send(embed=embed)
            return

        if action == "add":
            if resolved.id in no_prefix_users:
                embed = discord.Embed(
                    title="⚠️ Already Added",
                    description=f"{resolved.mention} is already in the no-prefix list.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                await ctx.send(embed=embed)
                return
            no_prefix_users.append(resolved.id)
        else:
            if resolved.id not in no_prefix_users:
                embed = discord.Embed(
                    title="⚠️ Not In List",
                    description=f"{resolved.mention} is not in the no-prefix list.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                await ctx.send(embed=embed)
                return
            no_prefix_users.remove(resolved.id)

        with open(NOPREFIX_FILE, "w") as f:
            json.dump(no_prefix_users, f, indent=2)

            embed = discord.Embed(
                title=f"✅ {action.title()}ed No-Prefix List",
                description=f"{resolved.mention} has been {action}ed to the no-prefix list.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Prefix(bot))
