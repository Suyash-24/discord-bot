import discord
from discord.ext import commands
import json
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN") 
DEFAULT_PREFIX = "!"



def load_no_prefix_users():
    if os.path.exists("no_prefix_users.json"):
        with open("no_prefix_users.json", "r") as f:
            return json.load(f)
    return [1105502119731150858] 

def save_no_prefix_users(data):
    with open("no_prefix_users.json", "w") as f:
        json.dump(data, f, indent=2)

NO_PREFIX_USERS = load_no_prefix_users()


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

   
    if message.author.id in NO_PREFIX_USERS:
        return (custom_prefix, "", f"<@!{bot.user.id}> ", f"<@{bot.user.id}> ")
    return (custom_prefix, f"<@!{bot.user.id}> ", f"<@{bot.user.id}> ")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True


bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# Custom help command styled like the example
@bot.command(name="help")
async def custom_help(ctx):
    guild = ctx.guild
    user = ctx.author
    icon_url = guild.icon.url if guild.icon else None
    banner_url = guild.banner.url if guild.banner else None

    embed = discord.Embed(
        description=(
            f"Hey! {user.mention},\n"
            f"It's **{guild.name}** here, your all-in-one server management & security partner.\n"
            f"Use `help` to unlock **unique features**."
        ),
        color=discord.Color.blurple()
    )

    # Set author with server icon (top right corner)
    embed.set_author(name=user.display_name, icon_url=icon_url)

    # Add server banner as image if available
    if banner_url:
        embed.set_image(url=banner_url)

    # Modules section (customize as needed)
    modules = [
        ("🔴 General", ""),
        ("🛠️ Moderation", ""),
        ("🤖 Automod", ""),
        ("✨ Extra", ""),
        ("🛡️ Security", ""),
        ("🎫 Ticket", ""),
        ("⭐ Starboard", ""),
        ("⚙️ Automation", ""),
        ("🚫 Ignore", ""),
        ("🎭 Reactionrole", ""),
        ("🖼️ Media", ""),
        ("🎉 Giveaway", ""),
        ("🔊 Voice Moderation", ""),
        ("🧩 Customrole", ""),
        ("🚀 Booster", ""),
        ("👋 Welcomer", ""),
        ("🛠️ Utility", ""),
        ("🎲 Fun", "")
    ]

    module_list = "\n".join([f"{emoji} {name}" for (emoji, name) in [(m.split(' ',1)[0], m.split(' ',1)[1]) if ' ' in m else (m, '') for m, _ in modules]])
    embed.add_field(
        name="📂 **Modules**",
        value=module_list,
        inline=False
    )

    # Premium section (optional)
    embed.add_field(
        name="<:premium:112233445566778899> **Premium**",
        value="Unlock more features with premium!",
        inline=False
    )

    await ctx.send(embed=embed)

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
        return await ctx.send("Usage: `np add @user` or `np remove @user`")

   
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