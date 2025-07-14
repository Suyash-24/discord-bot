import discord
from discord.ext import commands
import json
import os
from discord import ui, Interaction

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

    def load_no_prefix_users():
        if os.path.exists("no_prefix_users.json"):
            with open("no_prefix_users.json", "r") as f:
                return json.load(f)
        return [1105502119731150858]
    no_prefix_users = load_no_prefix_users()

    mention1 = f"<@!{bot.user.id}>"
    mention2 = f"<@{bot.user.id}>"
    prefixes = [custom_prefix, mention1, mention2]

    # For no-prefix users, allow both prefix and no prefix
    if message.author.id in no_prefix_users:
        # Only add the empty string if the message does NOT start with a valid prefix
        content = message.content or ""
        if not any(content.startswith(p) for p in prefixes):
            prefixes = ["", *prefixes]
    return prefixes

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True


bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# Custom help command styled like the example

# --- Help Command with Dropdown ---



class BackToMenuButton(ui.Button):
    def __init__(self, main_embed, modules):
        super().__init__(label="Back to Main Menu", style=discord.ButtonStyle.secondary)
        self.main_embed = main_embed
        self.modules = modules

    async def callback(self, interaction: Interaction):
        # Recreate the main menu view and embed
        view = ModuleView(self.modules, bot=interaction.client, main_embed=self.main_embed)
        view.clear_items()  # Remove any stacked items
        view.add_item(view.select)  # Add only the dropdown
        await interaction.response.edit_message(embed=self.main_embed, view=view)

class ModuleSelect(ui.Select):
    def __init__(self, modules, bot=None, main_embed=None):
        options = [
            discord.SelectOption(label=name, description=f"Show info about {name}", emoji=emoji)
            for emoji, name in modules
        ]
        super().__init__(placeholder="Select a module...", min_values=1, max_values=1, options=options)
        self.modules = modules
        self.bot = bot
        self.main_embed = main_embed

    async def callback(self, interaction: Interaction):
        selected = self.values[0]
        emoji = next((e for e, n in self.modules if n == selected), "❓")
        # If General, show all general commands
        if selected.lower() == "general" and self.bot:
            cog = self.bot.get_cog("General")
            commands_list = [
                f"`{cmd.name}`: {cmd.help or 'No description.'}"
                for cmd in cog.get_commands()
            ] if cog else ["No commands found."]
            embed = discord.Embed(
                title=f"{emoji} General Module",
                description=f"\n".join(commands_list),
                color=discord.Color.blurple()
            )
        else:
            embed = discord.Embed(
                title=f"{emoji} {selected} Module",
                description=f"Information about the **{selected}** module will go here.",
                color=discord.Color.blurple()
            )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url if hasattr(interaction.user, 'display_avatar') else interaction.user.avatar.url if interaction.user.avatar else None)
        # Add back button
        view = ModuleView(self.modules, bot=self.bot, main_embed=self.main_embed)
        view.clear_items()  # Remove any stacked items
        view.add_item(BackToMenuButton(self.main_embed, self.modules))  # Add only the back button
        await interaction.response.edit_message(embed=embed, view=view)


from typing import Optional

class ModuleView(ui.View):
    def __init__(self, modules, bot=None, main_embed=None, timeout=60):
        super().__init__(timeout=timeout)
        self.select = ModuleSelect(modules, bot=bot, main_embed=main_embed)
        self.add_item(self.select)
        self.message: Optional[discord.Message] = None
        self.bot = bot
        self.main_embed = main_embed

    async def on_timeout(self):
        self.select.disabled = True
        for child in self.children:
            if isinstance(child, (ui.Select, ui.Button)):
                child.disabled = True
        if self.message:
            embed = self.message.embeds[0].copy() if self.message.embeds else discord.Embed(description="This help menu has expired.")
            desc = embed.description or ""
            embed.description = ("This help menu has expired\n\n" + desc)
            await self.message.edit(embed=embed, view=self)

@bot.command(name="help")
async def custom_help(ctx):
    guild = ctx.guild
    user = ctx.author
    icon_url = guild.icon.url if guild.icon else None
    banner_url = guild.banner.url if guild.banner else None

    modules = [
        ("🔴", "General"),
        ("🛠️", "Moderation"),
        ("🤖", "Automod"),
        ("✨", "Extra"),
        ("🛡️", "Security"),
        ("🎫", "Ticket"),
        ("⭐", "Starboard"),
        ("⚙️", "Automation"),
        ("🚫", "Ignore"),
        ("🎭", "Reactionrole"),
        ("🖼️", "Media"),
        ("🎉", "Giveaway"),
        ("🔊", "Voice Moderation"),
        ("🧩", "Customrole"),
        ("🚀", "Booster"),
        ("👋", "Welcomer"),
        ("🛠️", "Utility"),
        ("🎲", "Fun")
    ]

    # Get the current prefix for this server
    prefix = prefix_db.get(str(guild.id), DEFAULT_PREFIX)

    bot_name = bot.user.name if bot.user else "This bot"
    embed = discord.Embed(
        description=(
            f"Hey! {user.mention},\n"
            f"This bot is made for **{guild.name}**.\n"
            f"Prefix for this server: `{prefix}`\n\n"
            f"**About:**\n"
            f"{bot_name} is a multipurpose Discord bot designed to help you manage, secure, and have fun in your server. "
            f"It features moderation, automod, tickets, giveaways, utility, and much more!\n\n"
        ),
        color=discord.Color.blurple()
    )
    # Set author (top left) and server icon as thumbnail (top right)
    embed.set_author(name=guild.name)
    if icon_url:
        embed.set_thumbnail(url=icon_url)
    embed.add_field(
        name="📂 **Modules**",
        value="Select a module from the dropdown below to view more info!",
        inline=False
    )
    embed.set_footer(text=f"Requested by {user.display_name}", icon_url=user.display_avatar.url if hasattr(user, 'display_avatar') else user.avatar.url if user.avatar else None)

    view = ModuleView(modules, bot=bot, main_embed=embed)
    sent = await ctx.send(embed=embed, view=view)
    view.message = sent



# Load cogs
import asyncio
cogs_loaded = False
@bot.event
async def on_ready():
    global cogs_loaded
    # Load cogs only once
    if not cogs_loaded:
        await bot.load_extension('cogs.general')
        await bot.load_extension('cogs.moderation')
        await bot.load_extension('cogs.muterole')
        cogs_loaded = True
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
async def np(ctx, action: str = "", member: str = ""):
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


# --- Global Error Handler ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        perms = ', '.join(error.missing_permissions)
        embed = discord.Embed(
            title="Missing Permissions",
            description=f"You are missing the following permission(s): `{perms}`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BotMissingPermissions):
        perms = ', '.join(error.missing_permissions)
        embed = discord.Embed(
            title="Bot Missing Permissions",
            description=f"I am missing the following permission(s): `{perms}`",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            title="Command Not Found",
            description=f"That command does not exist. Use `/help` or `{DEFAULT_PREFIX}help` to see all commands.",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
        # Show usage/help for the command
        cmd = ctx.command
        usage = f"{DEFAULT_PREFIX}{cmd.qualified_name} {cmd.signature}" if cmd else ""
        embed = discord.Embed(
            title=f"Command {cmd.name if cmd else ''}",
            description=cmd.help or "",
            color=discord.Color.orange()
        )
        if usage:
            embed.add_field(name="Usage", value=f"📒 Command Usage : `{usage}`", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
    else:
        # For any other error, print to console and send a generic error message
        print(f"[ERROR] {type(error).__name__}: {error}")
        embed = discord.Embed(
            title="Error",
            description=f"An unexpected error occurred: `{type(error).__name__}`\n{error}",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

if not TOKEN:
    raise RuntimeError("DISCORD_BOT_TOKEN environment variable not set.")
bot.run(TOKEN)