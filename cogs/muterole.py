import discord
from discord.ext import commands
from discord import app_commands
from utils import modutils
from discord.utils import get
import datetime
import json
import os

MUTEROLE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'muteroles.json')

def load_muteroles():
    if not os.path.exists(MUTEROLE_FILE):
        with open(MUTEROLE_FILE, 'w') as f:
            json.dump({}, f)
    with open(MUTEROLE_FILE, 'r') as f:
        return json.load(f)

def save_muteroles(data):
    with open(MUTEROLE_FILE, 'w') as f:
        json.dump(data, f, indent=2)


class MuteRole(commands.Cog):

    def get_muted_role(self, guild: discord.Guild):
        data = load_muteroles()
        role_id = data.get(str(guild.id))
        if role_id:
            return guild.get_role(role_id)
        return discord.utils.get(guild.roles, name="Muted")

    @commands.group(name="muterole", invoke_without_command=True)
    async def muterole_group(self, ctx):
        """Group for muterole management commands."""
        await ctx.send("Use `muterole create`, `muterole set <role>`, or `muterole info`.")

    @muterole_group.command(name="create")
    async def muterole_create(self, ctx):
        """Create a Muted role and set permissions (persistent)."""
        guild = ctx.guild
        if not guild:
            return await ctx.send("This command can only be used in a server.")
        data = load_muteroles()
        existing = self.get_muted_role(guild)
        if existing:
            return await ctx.send(f"A Muted role already exists: {existing.mention}")
        muted_role = await guild.create_role(name="Muted", reason="Mute role setup")
        for channel in guild.channels:
            await channel.set_permissions(muted_role, send_messages=False, speak=False, add_reactions=False)
        data[str(guild.id)] = muted_role.id
        save_muteroles(data)
        await ctx.send(f"✅ Created Muted role: {muted_role.mention}, set permissions, and saved persistently.")

    @muterole_group.command(name="set")
    async def muterole_set(self, ctx, role: discord.Role):
        """Set an existing role as the Muted role (persistent)."""
        guild = ctx.guild
        if not guild:
            return await ctx.send("This command can only be used in a server.")
        data = load_muteroles()
        data[str(guild.id)] = role.id
        save_muteroles(data)
        await ctx.send(f"✅ Set {role.mention} as the Muted role and saved persistently.")

    @muterole_group.command(name="info")
    async def muterole_info(self, ctx):
        """Show info about the current Muted role (persistent)."""
        guild = ctx.guild
        if not guild:
            return await ctx.send("This command can only be used in a server.")
        muted_role = self.get_muted_role(guild)
        if not muted_role:
            return await ctx.send("No Muted role found.")
        perms = muted_role.permissions
        await ctx.send(f"Muted role: {muted_role.mention}\nPermissions: {perms}")

    # Slash command versions
    @app_commands.command(name="muterole_create", description="Create a Muted role and set permissions.")
    async def muterole_create_slash(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        data = load_muteroles()
        existing = self.get_muted_role(guild)
        if existing:
            return await interaction.response.send_message(f"A Muted role already exists: {existing.mention}", ephemeral=True)
        muted_role = await guild.create_role(name="Muted", reason="Mute role setup")
        for channel in guild.channels:
            await channel.set_permissions(muted_role, send_messages=False, speak=False, add_reactions=False)
        data[str(guild.id)] = muted_role.id
        save_muteroles(data)
        await interaction.response.send_message(f"✅ Created Muted role: {muted_role.mention}, set permissions, and saved persistently.", ephemeral=True)

    @app_commands.command(name="muterole_set", description="Set an existing role as the Muted role.")
    async def muterole_set_slash(self, interaction: discord.Interaction, role: discord.Role):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        data = load_muteroles()
        data[str(guild.id)] = role.id
        save_muteroles(data)
        await interaction.response.send_message(f"✅ Set {role.mention} as the Muted role and saved persistently.", ephemeral=True)

    @app_commands.command(name="muterole_info", description="Show info about the current Muted role.")
    async def muterole_info_slash(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        muted_role = self.get_muted_role(guild)
        if not muted_role:
            return await interaction.response.send_message("No Muted role found.", ephemeral=True)
        perms = muted_role.permissions
        await interaction.response.send_message(f"Muted role: {muted_role.mention}\nPermissions: {perms}", ephemeral=True)
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(MuteRole(bot))

