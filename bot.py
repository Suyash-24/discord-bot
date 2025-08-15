
import discord
from discord.ext import commands

import os
import asyncio
from dotenv import load_dotenv

# Ensure required data files exist
required_files = [
    "data/modroles.json",
    "data/modlogs.json",
    "data/muteroles.json",
    "data/active_mutes.json",
    "data/warnings.json"
]
for file in required_files:
    dir_path = os.path.dirname(file)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    if not os.path.exists(file):
        with open(file, "w") as f:
            f.write("{}" if file.endswith(".json") else "")

load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")
if BOT_TOKEN is None:
    raise ValueError("TOKEN is not set. Please check your environment variables.")

# Import get_prefix from cogs.prefix
import sys
import importlib.util
prefix_path = os.path.join(os.path.dirname(__file__), "cogs", "prefix.py")
spec = importlib.util.spec_from_file_location("prefix", prefix_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load spec for prefix.py at {prefix_path}")
prefix_mod = importlib.util.module_from_spec(spec)
sys.modules["prefix"] = prefix_mod
spec.loader.exec_module(prefix_mod)
if not hasattr(prefix_mod, "get_prefix"):
    raise ImportError("get_prefix not found in cogs/prefix.py")
get_prefix = prefix_mod.get_prefix

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    synced = await bot.tree.sync()
    print(f"✅ Synced {len(synced)} slash commands.")


# Global error handler for prefix commands
@bot.event
async def on_command_error(ctx, error):
    usage = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}" if hasattr(ctx, 'command') and ctx.command else None
    # Style for missing arguments and failed checks
    if isinstance(error, commands.MissingRequiredArgument):
        embed = discord.Embed(
            description=f"⚠️ | **Please provide required arguments**\n**Use :** `{usage}`",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, delete_after=8)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            description=f"⚠️ | **Bad argument:** {str(error)}\n**Use :** `{usage}`",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, delete_after=8)
    elif isinstance(error, commands.MissingPermissions):
        perms = getattr(error, 'missing_perms', None)
        if perms:
            perms_str = ', '.join(f'`{p.replace("_", " ").title()}`' for p in perms)
            desc = f"❌ | **Missing Permissions:** {perms_str}"
        else:
            desc = "❌ | **You don't have permission to use this command.**"
        embed = discord.Embed(
            description=desc,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=8)
    elif error.__class__.__name__ == "NotModError":
        embed = discord.Embed(
            description="❌ | **You don't have permission to use this command.**",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=8)
    elif isinstance(error, commands.CheckFailure):
        embed = discord.Embed(
            description=f"⚠️ | **Please provide required arguments**\n**Use :** `{usage}`" if usage else "⚠️ | **You don't have permission to use this command.**",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, delete_after=8)
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        embed = discord.Embed(
            description=f"❌ | {str(error)}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed, delete_after=8)


# Respond when the bot is mentioned directly
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    # Wait until bot.user is available
    if not bot.user:
        await bot.wait_until_ready()
    # If the message is only a mention of the bot (no other text)
    if bot.user and message.content.strip() in [f'<@{bot.user.id}>', f'<@!{bot.user.id}>']:
        prefix = (await bot.get_prefix(message))
        if isinstance(prefix, (list, tuple)):
            prefix = prefix[0]
        display_name = getattr(bot.user, 'display_name', bot.user.name)
        embed = discord.Embed(
            title=f"👋 Hi, I'm {display_name}!",
            description=f"My prefix here is `{prefix}`.\nType `{prefix}help` to see my commands!",
            color=discord.Color.blurple()
        )
        await message.channel.send(embed=embed)
        return
    await bot.process_commands(message)


async def main():
    print("[Startup] Starting bot...")
    try:
        async with bot:
            print("[Startup] Loading cogs.prefix")
            await bot.load_extension("cogs.prefix")
            print("[Startup] Loading cogs.general")
            await bot.load_extension("cogs.general")
            print("[Startup] Loading cogs.moderation")
            await bot.load_extension("cogs.moderation")
            print("[Startup] Loading cogs.automod")
            await bot.load_extension("cogs.automod")
            print("[Startup] Loading cogs.events")
            await bot.load_extension("cogs.events")
            print("[Startup] Loading cogs.muterole")
            await bot.load_extension("cogs.muterole")
            print("[Startup] Loading cogs.help_command")
            await bot.load_extension("cogs.help_command")
            print("[Startup] Loading cogs.welcome")
            await bot.load_extension("cogs.welcome")

            print("[Startup] Loading cogs.customroles")
            await bot.load_extension("cogs.customroles")
            print("[Startup] Loading cogs.expressions")
            await bot.load_extension("cogs.expressions")
            print("[Startup] Loading cogs.stats")
            await bot.load_extension("cogs.stats")
            print("[Startup] All cogs loaded. Starting bot event loop...")
            assert BOT_TOKEN is not None, "TOKEN is not set. Please check your environment variables."
            await bot.start(BOT_TOKEN)
    except Exception as e:
        import traceback
        print("[Startup Error]", e)
        traceback.print_exc()

asyncio.run(main())
bot.run(BOT_TOKEN)