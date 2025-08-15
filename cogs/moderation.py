import discord
import typing
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import datetime
import json, os

# Safe dynamic import of muterole.py for persistent Muted role logic
import sys
import importlib.util
import_path = os.path.join(os.path.dirname(__file__), 'muterole.py')
muterole_spec = importlib.util.spec_from_file_location("muterole", import_path)
if muterole_spec is None or muterole_spec.loader is None:
    raise ImportError(f"Could not load muterole.py at {import_path}")
muterole_mod = importlib.util.module_from_spec(muterole_spec)
sys.modules["muterole"] = muterole_mod
muterole_spec.loader.exec_module(muterole_mod)
load_muteroles = muterole_mod.load_muteroles

from typing import Optional
from utils.modutils import is_mod_user, log_mod_action

# Custom exception for mod check
class NotModError(commands.CheckFailure):
    pass

WARN_FILE = "data/warnings.json"
if not os.path.exists(WARN_FILE):
    with open(WARN_FILE, "w") as f:
        json.dump({}, f)

class Moderation(commands.Cog):
    def load_active_mutes(self):
        import json, os
        path = os.path.join(os.path.dirname(__file__), '..', 'data', 'active_mutes.json')
        if not os.path.exists(path):
            with open(path, 'w') as f:
                json.dump({}, f)
        with open(path, 'r') as f:
            return json.load(f)

    def save_active_mutes(self, mutes):
        import json, os
        path = os.path.join(os.path.dirname(__file__), '..', 'data', 'active_mutes.json')
        with open(path, 'w') as f:
            json.dump(mutes, f, indent=2)

    async def unmute_expired(self):
        import time
        mutes = self.load_active_mutes()
        changed = False
        for guild_id, members in list(mutes.items()):
            guild = self.bot.get_guild(int(guild_id))
            if not guild:
                continue
            role = self.get_muted_role(guild)
            for user_id, mute_info in list(members.items()):
                if mute_info['until'] <= time.time():
                    member = guild.get_member(int(user_id))
                    if member and role in member.roles:
                        try:
                            await member.remove_roles(role, reason="Mute duration expired.")
                            await log_mod_action(guild, "unmute", member, member, "Mute duration expired.")
                        except Exception:
                            pass
                    del mutes[guild_id][user_id]
                    changed = True
            if not mutes[guild_id]:
                del mutes[guild_id]
        if changed:
            self.save_active_mutes(mutes)

    async def mute_watcher(self):
        import asyncio
        while True:
            await self.unmute_expired()
            await asyncio.sleep(60)

    async def cog_load(self):
        # Start mute watcher on cog load
        self.bot.loop.create_task(self.mute_watcher())
    def get_muted_role(self, guild: discord.Guild):
        data = load_muteroles()
        role_id = data.get(str(guild.id))
        if role_id:
            return guild.get_role(role_id)
        return discord.utils.get(guild.roles, name="Muted")
    # ----- SLASH COMMANDS -----

    @app_commands.command(name="ban", description="Ban a member")
    @app_commands.checks.has_permissions(ban_members=True)
    async def slash_ban(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = None):
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not is_mod_user(moderator):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        await member.ban(reason=reason)
        await log_mod_action(guild, "ban", moderator, member, reason)
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"{member.mention} was banned.\n**Reason:** {reason or 'No reason provided.'}",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unban", description="Unban a user (username#discriminator)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def slash_unban(self, interaction: discord.Interaction, user: str):
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not is_mod_user(moderator):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        name, discrim = user.split("#")
        async for entry in guild.bans():
            u = entry.user
            if u.name == name and u.discriminator == discrim:
                await guild.unban(u)
                await log_mod_action(guild, "unban", moderator, u, f"Unbanned user: {u} ({u.id})")
                embed = discord.Embed(
                    title="✅ Member Unbanned",
                    description=f"{u.mention} has been unbanned.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
                return await interaction.response.send_message(embed=embed, ephemeral=True)
        embed = discord.Embed(
            title="❌ User Not Found",
            description="User not found in ban list.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="warn", description="Warn a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def slash_warn(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = None):
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not is_mod_user(moderator):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        guild_id = str(guild.id)
        who = str(member.id)
        with open(WARN_FILE, "r") as f:
            data = json.load(f)
        data.setdefault(guild_id, {}).setdefault(who, []).append(reason or "No reason")
        with open(WARN_FILE, "w") as f:
            json.dump(data, f, indent=2)
        await log_mod_action(guild, "warn", moderator, member, reason)
        embed = discord.Embed(
            title="⚠️ Member Warned",
            description=f"{member.mention} was warned.\n**Reason:** {reason or 'No reason provided.'}",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="warnings", description="Show warnings for a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def slash_warnings(self, interaction: discord.Interaction, member: discord.Member):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        with open(WARN_FILE, "r") as f:
            data = json.load(f)
        warnings = data.get(str(guild.id), {}).get(str(member.id), [])
        msg = "\n".join(warnings) if warnings else "No warnings."
        embed = discord.Embed(
            title="📋 Warnings",
            description=f"{member.mention} has {len(warnings)} warning(s).\n{msg}",
            color=discord.Color.yellow(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url if hasattr(interaction.user, 'display_avatar') else interaction.user.avatar.url if interaction.user.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clear", description="Clear messages in a channel")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def slash_clear(self, interaction: discord.Interaction, amount: int):
        channel = interaction.channel
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("❌ No permission or invalid channel", ephemeral=True)
        deleted = await channel.purge(limit=amount + 1)
        await log_mod_action(guild, "clear", moderator, moderator, f"Deleted {len(deleted)} messages")
        embed = discord.Embed(
            title="🧹 Messages Cleared",
            description=f"Cleared {len(deleted)} messages.",
            color=discord.Color.teal(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="mute", description="Mute a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def slash_mute(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = None):
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not is_mod_user(moderator):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        role = self.get_muted_role(guild)
        if not role:
            role = await guild.create_role(name="Muted")
            for ch in guild.channels:
                await ch.set_permissions(role, send_messages=False, speak=False)
            # Save to persistent storage
            data = load_muteroles()
            data[str(guild.id)] = role.id
            muterole_mod.save_muteroles(data)
        await member.add_roles(role, reason=reason)
        await log_mod_action(guild, "mute", moderator, member, reason)
        embed = discord.Embed(
            title="🔇 Member Muted",
            description=f"{member.mention} was muted.\n**Reason:** {reason or 'No reason provided.'}",
            color=discord.Color.dark_purple(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unmute", description="Unmute a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def slash_unmute(self, interaction: discord.Interaction, member: discord.Member):
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not is_mod_user(moderator):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        role = self.get_muted_role(guild)
        if role:
            await member.remove_roles(role)
        await log_mod_action(guild, "unmute", moderator, member)
        embed = discord.Embed(
            title="🔊 Member Unmuted",
            description=f"{member.mention} was unmuted.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="lock", description="Lock the current channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slash_lock(self, interaction: discord.Interaction):
        channel = interaction.channel
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("❌ No permission or invalid channel", ephemeral=True)
        await channel.set_permissions(guild.default_role, send_messages=False)
        await log_mod_action(guild, "lock", moderator, moderator)
        embed = discord.Embed(
            title="🔒 Channel Locked",
            description="This channel is now locked.",
            color=discord.Color.dark_grey(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="unlock", description="Unlock the current channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slash_unlock(self, interaction: discord.Interaction):
        channel = interaction.channel
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("❌ No permission or invalid channel", ephemeral=True)
        await channel.set_permissions(guild.default_role, send_messages=True)
        await log_mod_action(guild, "unlock", moderator, moderator)
        embed = discord.Embed(
            title="🔓 Channel Unlocked",
            description="This channel is now unlocked.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="slowmode", description="Set slowmode for the current channel")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slash_slowmode(self, interaction: discord.Interaction, seconds: int):
        channel = interaction.channel
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message("❌ No permission or invalid channel", ephemeral=True)
        await channel.edit(slowmode_delay=seconds)
        await log_mod_action(guild, "slowmode", moderator, moderator, f"{seconds}s")
        embed = discord.Embed(
            title="🐢 Slowmode Set",
            description=f"Slowmode set to {seconds} seconds.",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="timeout", description="Timeout a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def slash_timeout(self, interaction: discord.Interaction, member: discord.Member, seconds: int, reason: Optional[str] = "No reason"):
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not is_mod_user(moderator):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        until = discord.utils.utcnow() + timedelta(seconds=seconds)
        await member.edit(timed_out_until=until, reason=reason)
        await log_mod_action(guild, "timeout", moderator, member, reason)
        embed = discord.Embed(
            title="⏱️ Member Timed Out",
            description=f"{member.mention} was timed out for {seconds} seconds.\n**Reason:** {reason}",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def slash_untimeout(self, interaction: discord.Interaction, member: discord.Member):
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not is_mod_user(moderator):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        await member.edit(timed_out_until=None)
        await log_mod_action(guild, "untimeout", moderator, member)
        embed = discord.Embed(
            title="✅ Timeout Removed",
            description=f"Timeout removed for {member.mention}.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="nickname", description="Change a member's nickname")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def slash_nickname(self, interaction: discord.Interaction, member: discord.Member, nickname: Optional[str] = None):
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not is_mod_user(moderator):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        await member.edit(nick=nickname)
        await log_mod_action(guild, "nickname", moderator, member, nickname)
        embed = discord.Embed(
            title="📝 Nickname Changed",
            description=f"Nickname changed for {member.mention} to `{nickname}`.",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="roleadd", description="Add a role to a member")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def slash_roleadd(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not is_mod_user(moderator):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        await member.add_roles(role)
        await log_mod_action(guild, "roleadd", moderator, member, role.name)
        embed = discord.Embed(
            title="✅ Role Added",
            description=f"Added `{role.name}` to {member.mention}.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="roleremove", description="Remove a role from a member")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def slash_roleremove(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        guild = interaction.guild
        moderator = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not guild or not moderator or not is_mod_user(moderator):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        await member.remove_roles(role)
        await log_mod_action(guild, "roleremove", moderator, member, role.name)
        embed = discord.Embed(
            title="❌ Role Removed",
            description=f"Removed `{role.name}` from {member.mention}.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {moderator.display_name}", icon_url=moderator.display_avatar.url if hasattr(moderator, 'display_avatar') else moderator.avatar.url if moderator.avatar else None)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    def __init__(self, bot):
        self.bot = bot
        self._mute_watcher_started = False

    @staticmethod
    def mod_check():
        def predicate(ctx):
            if not is_mod_user(ctx.author):
                raise NotModError()
            return True
        return commands.check(predicate)

    # ----- PREFIX COMMANDS -----

    @commands.command()
    @mod_check()
    async def kick(self, ctx, member: typing.Union[discord.Member, str, int], *, reason=None):
        resolved = None
        if isinstance(member, discord.Member):
            resolved = member
        else:
            try:
                member_id = int(member)
                resolved = ctx.guild.get_member(member_id)
            except Exception:
                await ctx.send("❌ Could not find a member with that ID.")
                return
        if not resolved:
            await ctx.send("❌ Could not resolve member.")
            return
        await resolved.kick(reason=reason)
        await log_mod_action(ctx.guild, "kick", ctx.author, resolved, reason)
        embed = discord.Embed(
            title="👢 Member Kicked",
            description=f"{resolved.mention} was kicked.\n**Reason:** {reason or 'No reason provided.'}",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @mod_check()
    async def ban(self, ctx, member: typing.Union[discord.Member, str, int], *, reason=None):
        resolved = None
        if isinstance(member, discord.Member):
            resolved = member
        else:
            try:
                member_id = int(member)
                resolved = ctx.guild.get_member(member_id)
            except Exception:
                await ctx.send("❌ Could not find a member with that ID.")
                return
        if not resolved:
            await ctx.send("❌ Could not resolve member.")
            return
        await resolved.ban(reason=reason)
        await log_mod_action(ctx.guild, "ban", ctx.author, resolved, reason)
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"{resolved.mention} was banned.\n**Reason:** {reason or 'No reason provided.'}",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @mod_check()
    async def unban(self, ctx, *, user: str):
        name, discrim = user.split("#")
        for entry in await ctx.guild.bans():
            u = entry.user
            if u.name == name and u.discriminator == discrim:
                await ctx.guild.unban(u)
                await log_mod_action(ctx.guild, "unban", ctx.author, u)
                embed = discord.Embed(
                    title="✅ Member Unbanned",
                    description=f"{u.mention} has been unbanned.",
                    color=discord.Color.green(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
                return await ctx.send(embed=embed)
        embed = discord.Embed(
            title="❌ User Not Found",
            description="User not found in ban list.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        await ctx.send(embed=embed)

    @commands.command()
    @mod_check()
    async def warn(self, ctx, member: typing.Union[discord.Member, str, int], *, reason=None):
        resolved = None
        if isinstance(member, discord.Member):
            resolved = member
        else:
            try:
                member_id = int(member)
                resolved = ctx.guild.get_member(member_id)
            except Exception:
                await ctx.send("❌ Could not find a member with that ID.")
                return
        if not resolved:
            await ctx.send("❌ Could not resolve member.")
            return
        with open(WARN_FILE, "r") as f:
            data = json.load(f)
        guild = str(ctx.guild.id)
        who = str(resolved.id)
        data.setdefault(guild, {}).setdefault(who, []).append(reason or "No reason")
        with open(WARN_FILE, "w") as f:
            json.dump(data, f, indent=2)

        await log_mod_action(ctx.guild, "warn", ctx.author, resolved, reason)
        embed = discord.Embed(
            title="⚠️ Member Warned",
            description=f"{resolved.mention} was warned.\n**Reason:** {reason or 'No reason provided.'}",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @mod_check()
    async def warnings(self, ctx, member: discord.Member):
        with open(WARN_FILE, "r") as f:
            data = json.load(f)
        warnings = data.get(str(ctx.guild.id), {}).get(str(member.id), [])
        msg = "\n".join(warnings) if warnings else "No warnings."
        embed = discord.Embed(
            title="📋 Warnings",
            description=f"{member.mention} has {len(warnings)} warning(s).\n{msg}",
            color=discord.Color.yellow(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @mod_check()
    async def clear(self, ctx, amount: int):
        deleted = await ctx.channel.purge(limit=amount + 1)
        await log_mod_action(ctx.guild, "clear", ctx.author, ctx.author, f"Deleted {len(deleted)} messages")
        embed = discord.Embed(
            title="🧹 Messages Cleared",
            description=f"Cleared {len(deleted)} messages.",
            color=discord.Color.teal(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed, delete_after=3)

    # (Removed duplicate softban command)

    @commands.command()
    @mod_check()
    async def mute(self, ctx, member: discord.Member, duration: Optional[str] = None, *, reason=None):
        """
        Mute a member for a duration (e.g., 1d, 2h, 30m). If no duration, mute is indefinite.
        """
        import re, time
        role = self.get_muted_role(ctx.guild)
        if not role:
            role = await ctx.guild.create_role(name="Muted")
            for ch in ctx.guild.channels:
                await ch.set_permissions(role, send_messages=False, speak=False)
            # Save to persistent storage
            data = load_muteroles()
            data[str(ctx.guild.id)] = role.id
            muterole_mod.save_muteroles(data)
        await member.add_roles(role, reason=reason)
        await log_mod_action(ctx.guild, "mute", ctx.author, member, reason)
        desc = f"{member.mention} was muted."
        if duration:
            desc += f"\n**Duration:** {duration}"
        desc += f"\n**Reason:** {reason or 'No reason provided.'}"
        embed = discord.Embed(
            title="🔇 Member Muted",
            description=desc,
            color=discord.Color.dark_purple(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

        # Parse duration and persist mute
        if duration:
            seconds = 0
            pattern = r"(\d+)([dhms])"
            for amount, unit in re.findall(pattern, duration.lower()):
                amount = int(amount)
                if unit == 'd':
                    seconds += amount * 86400
                elif unit == 'h':
                    seconds += amount * 3600
                elif unit == 'm':
                    seconds += amount * 60
                elif unit == 's':
                    seconds += amount
            if seconds > 0:
                mutes = self.load_active_mutes()
                guild_id = str(ctx.guild.id)
                user_id = str(member.id)
                until = time.time() + seconds
                if guild_id not in mutes:
                    mutes[guild_id] = {}
                mutes[guild_id][user_id] = {"until": until, "reason": reason or "Mute duration"}
                self.save_active_mutes(mutes)

    @commands.command()
    @mod_check()
    async def unmute(self, ctx, member: discord.Member):
        role = self.get_muted_role(ctx.guild)
        if role:
            await member.remove_roles(role)
        await log_mod_action(ctx.guild, "unmute", ctx.author, member)
        embed = discord.Embed(
            title="🔊 Member Unmuted",
            description=f"{member.mention} was unmuted.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
        # Remove from persistent mutes if present
        mutes = self.load_active_mutes()
        guild_id = str(ctx.guild.id)
        user_id = str(member.id)
        changed = False
        if guild_id in mutes and user_id in mutes[guild_id]:
            del mutes[guild_id][user_id]
            if not mutes[guild_id]:
                del mutes[guild_id]
            changed = True
        if changed:
            self.save_active_mutes(mutes)

    @commands.command()
    @mod_check()
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await log_mod_action(ctx.guild, "lock", ctx.author, ctx.author)
        embed = discord.Embed(
            title="🔒 Channel Locked",
            description="This channel is now locked.",
            color=discord.Color.dark_grey(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @mod_check()
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await log_mod_action(ctx.guild, "unlock", ctx.author, ctx.author)
        embed = discord.Embed(
            title="🔓 Channel Unlocked",
            description="This channel is now unlocked.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @mod_check()
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        await log_mod_action(ctx.guild, "slowmode", ctx.author, ctx.author, f"{seconds}s")
        embed = discord.Embed(
            title="🐢 Slowmode Set",
            description=f"Slowmode set to {seconds} seconds.",
            color=discord.Color.blue(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @mod_check()
    async def timeout(self, ctx, member: discord.Member, seconds: int, *, reason="No reason"):
        until = discord.utils.utcnow() + timedelta(seconds=seconds)
        await member.edit(timed_out_until=until, reason=reason)
        await log_mod_action(ctx.guild, "timeout", ctx.author, member, reason)
        embed = discord.Embed(
            title="⏱️ Member Timed Out",
            description=f"{member.mention} was timed out for {seconds} seconds.\n**Reason:** {reason}",
            color=discord.Color.orange(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command(name="unmute_member")
    @mod_check()
    async def unmute_member(self, ctx, member: discord.Member):
        role = self.get_muted_role(ctx.guild)
        if role:
            await member.remove_roles(role)
        await log_mod_action(ctx.guild, "unmute", ctx.author, member)
        embed = discord.Embed(
            title="🔊 Member Unmuted",
            description=f"{member.mention} was unmuted.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
    @mod_check()
    async def nickname(self, ctx, member: discord.Member, *, nickname: Optional[str] = None):
        await member.edit(nick=nickname)
        await log_mod_action(ctx.guild, "nickname", ctx.author, member, nickname)
        embed = discord.Embed(
            title="📝 Nickname Changed",
            description=f"Nickname changed for {member.mention} to `{nickname}`.",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @mod_check()
    async def roleadd(self, ctx, member: discord.Member, *, role: discord.Role):
        await member.add_roles(role)
        await log_mod_action(ctx.guild, "roleadd", ctx.author, member, role.name)
        embed = discord.Embed(
            title="✅ Role Added",
            description=f"Added `{role.name}` to {member.mention}.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @mod_check()
    async def roleremove(self, ctx, member: discord.Member, *, role: discord.Role):
        await member.remove_roles(role)
        await log_mod_action(ctx.guild, "roleremove", ctx.author, member, role.name)
        embed = discord.Embed(
            title="❌ Role Removed",
            description=f"Removed `{role.name}` from {member.mention}.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Action by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    # (Removed duplicate softban command)

    # ----- SLASH COMMANDS -----

    @app_commands.command(name="kick", description="Kick a member")
    @app_commands.checks.has_permissions(kick_members=True)
    async def slash_kick(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = None):
        guild = interaction.guild
        if not guild or not isinstance(interaction.user, discord.Member) or not is_mod_user(interaction.user):
            return await interaction.response.send_message("❌ No permission", ephemeral=True)
        await member.kick(reason=reason)
        await log_mod_action(guild, "kick", interaction.user, member, reason)
        await interaction.response.send_message(f"👢 Kicked {member.mention}")

    # 📌 Create slash commands similarly for ban, unban, warn, clear, mute, unmute, etc.

async def setup(bot):
    cog = Moderation(bot)
    await bot.add_cog(cog)
    # Start mute watcher only once
    if not getattr(cog, '_mute_watcher_started', False):
        bot.loop.create_task(cog.mute_watcher())
        cog._mute_watcher_started = True
