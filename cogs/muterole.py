
print('[MUTEROLE] muterole.py imported')
import discord

from typing import Optional
from discord.ext import commands
import json
import os

MUTEROLE_FILE = "muteroles.json"

def load_muteroles():
    if os.path.exists(MUTEROLE_FILE):
        with open(MUTEROLE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_muteroles(data):
    with open(MUTEROLE_FILE, "w") as f:
        json.dump(data, f, indent=2)


# Store muteroles globally for use in mute/unmute
muteroles = load_muteroles()

class MuteRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.muteroles = muteroles

    @commands.group(invoke_without_command=True)
    async def muterole(self, ctx):
        """Manage the mute role for this server."""
        role_id = self.muteroles.get(str(ctx.guild.id))
        if role_id:
            role = ctx.guild.get_role(role_id)
            await ctx.send(f"Mute role for this server is set to: {role.mention if role else 'Unknown role'}.")
        else:
            await ctx.send("No mute role set for this server. Use `muterole create <name>` or `muterole set <@role>`.")

    @muterole.command()
    @commands.has_permissions(administrator=True)
    async def create(self, ctx, *, name: str = "Muted"):
        """Creates a new mute role and sets it as the mute role."""
        guild = ctx.guild
        existing = discord.utils.get(guild.roles, name=name)
        if existing:
            await ctx.send(f"A role named `{name}` already exists. Use `muterole set @{name}` to set it as the mute role.")
            return
        perms = discord.Permissions(send_messages=False, speak=False, add_reactions=False)
        role = await guild.create_role(name=name, permissions=perms, reason="Mute role created by bot")
        for channel in guild.channels:
            try:
                await channel.set_permissions(role, send_messages=False, speak=False, add_reactions=False)
            except Exception:
                pass
        self.muteroles[str(guild.id)] = role.id
        save_muteroles(self.muteroles)
        await ctx.send(f"Mute role `{name}` created and set as mute role.")

    @muterole.command()
    @commands.has_permissions(administrator=True)
    async def set(self, ctx, role: discord.Role):
        """Sets an existing role as the mute role."""
        self.muteroles[str(ctx.guild.id)] = role.id
        save_muteroles(self.muteroles)
        await ctx.send(f"Mute role set to {role.mention}.")

    @muterole.command()
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx):
        """Removes the mute role setting for this server."""
        if str(ctx.guild.id) in self.muteroles:
            del self.muteroles[str(ctx.guild.id)]
            save_muteroles(self.muteroles)
            await ctx.send("Mute role removed for this server.")
        else:
            await ctx.send("No mute role set for this server.")


    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, duration: Optional[str] = None, *, reason: Optional[str] = None):
        """
        Mute a member by assigning the mute role.
        Optionally specify a duration (e.g. 10m, 2h, 30s).
        Usage: !mute @user [duration] [reason]
        Example: !mute @user 10m spamming
        """
        import re
        import asyncio
        role_id = self.muteroles.get(str(ctx.guild.id))
        if not role_id:
            await ctx.send("No mute role set. Use `muterole create <name>` or `muterole set <@role>` first.")
            return
        role = ctx.guild.get_role(role_id)
        if not role:
            await ctx.send("Mute role not found. Please set it again.")
            return
        if role in member.roles:
            await ctx.send(f"{member.mention} is already muted.")
            return

        # Parse duration
        seconds = None
        if duration:
            match = re.match(r"^(\d+)([smhd])$", duration.strip().lower())
            if match:
                num, unit = match.groups()
                num = int(num)
                if unit == 's':
                    seconds = num
                elif unit == 'm':
                    seconds = num * 60
                elif unit == 'h':
                    seconds = num * 60 * 60
                elif unit == 'd':
                    seconds = num * 60 * 60 * 24
            else:
                # If duration is not valid, treat as part of reason
                reason = (duration + ' ' + (reason or '')).strip()
                seconds = None

        try:
            await member.add_roles(role, reason=reason or "Muted by command")
            msg = f"🔇 {member.mention} has been muted."
            if seconds:
                msg += f" Duration: {duration}"
            msg += f" Reason: {reason or 'No reason provided.'}"
            await ctx.send(msg)
            if seconds:
                await asyncio.sleep(seconds)
                # Check if still muted and unmute
                if role in member.roles:
                    try:
                        await member.remove_roles(role, reason="Timed mute expired")
                        await ctx.send(f"🔊 {member.mention} has been automatically unmuted after {duration}.")
                    except Exception:
                        pass
        except discord.Forbidden:
            await ctx.send("I do not have permission to add the mute role to this user.")
        except Exception as e:
            await ctx.send(f"Failed to mute: {e}")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        role_id = self.muteroles.get(str(ctx.guild.id))
        if not role_id:
            await ctx.send("No mute role set. Use `muterole create <name>` or `muterole set <@role>` first.")
            return
        role = ctx.guild.get_role(role_id)
        if not role:
            await ctx.send("Mute role not found. Please set it again.")
            return
        if role not in member.roles:
            await ctx.send(f"{member.mention} is not muted.")
            return
        try:
            await member.remove_roles(role, reason="Unmuted by command")
            await ctx.send(f"🔊 {member.mention} has been unmuted.")
        except discord.Forbidden:
            await ctx.send("I do not have permission to remove the mute role from this user.")
        except Exception as e:
            await ctx.send(f"Failed to unmute: {e}")

async def setup(bot):
    print("[MUTEROLE] Cog setup called.")
    await bot.add_cog(MuteRole(bot))
