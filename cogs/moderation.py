import discord
from discord.ext import commands
from typing import Optional
from discord import ui

class Moderation(commands.Cog):
    """Moderation commands for server management."""
    def __init__(self, bot):
        self.bot = bot

    # --- Moderation Commands ---
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: Optional[str] = None):
        """Kicks a user from the server."""
        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} was kicked.\nReason: {reason or 'No reason provided.'}",
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Could not kick {member.mention}: {e}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: Optional[str] = None):
        """Bans a user from the server."""
        try:
            await member.ban(reason=reason)
            embed = discord.Embed(
                title="Member Banned",
                description=f"{member.mention} was banned.\nReason: {reason or 'No reason provided.'}",
                color=discord.Color.red()
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Could not ban {member.mention}: {e}")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int):
        """Unbans a user by their ID."""
        user = await self.bot.fetch_user(user_id)
        try:
            await ctx.guild.unban(user)
            embed = discord.Embed(
                title="Member Unbanned",
                description=f"{user.mention} was unbanned.",
                color=discord.Color.green()
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Could not unban {user.mention}: {e}")

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx, member: discord.Member, *, reason: Optional[str] = None):
        """Warns a user (can be logged)."""
        embed = discord.Embed(
            title="User Warned",
            description=f"{member.mention} was warned.\nReason: {reason or 'No reason provided.'}",
            color=discord.Color.yellow()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)
        # TODO: Log warning


    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, time: Optional[str] = None):
        """Places user in timeout (Discord's native timeout)."""
        # TODO: Implement timeout
        await ctx.send(f"Timeout command for {member.mention} (time: {time}) is not yet implemented.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        """Sets slowmode delay in the current channel."""
        await ctx.channel.edit(slowmode_delay=seconds)
        embed = discord.Embed(
            title="Slowmode Set",
            description=f"Slowmode set to `{seconds}` seconds.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Deletes a number of recent messages."""
        if amount < 1 or amount > 100:
            return await ctx.send("❌ Please specify an amount between 1 and 100.")
        deleted = await ctx.channel.purge(limit=amount)
        embed = discord.Embed(
            title="Messages Cleared",
            description=f"Deleted `{len(deleted)}` messages.",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, member: discord.Member, amount: int):
        """Deletes a specific number of messages from a user."""
        # TODO: Implement user-specific purge
        await ctx.send(f"Purge command for {member.mention} (amount: {amount}) is not yet implemented.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        """Locks the current channel for @everyone."""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = False
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(
            title="Channel Locked",
            description="This channel has been locked for @everyone.",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        """Unlocks the current channel for @everyone."""
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.send_messages = True
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        embed = discord.Embed(
            title="Channel Unlocked",
            description="This channel has been unlocked for @everyone.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def nuke(self, ctx):
        """Deletes and clones the current channel (wipes it clean)."""
        channel = ctx.channel
        new_channel = await channel.clone(reason="Nuke command used.")
        await channel.delete()
        embed = discord.Embed(
            title="Channel Nuked",
            description=f"{new_channel.mention} has been nuked and recreated.",
            color=discord.Color.red()
        )
        await new_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member, *, role_name: str):
        """Adds a role to a user."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role `{role_name}` not found.")
        await member.add_roles(role)
        embed = discord.Embed(
            title="Role Added",
            description=f"Added role `{role_name}` to {member.mention}.",
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def derole(self, ctx, member: discord.Member, *, role_name: str):
        """Removes a role from a user."""
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            return await ctx.send(f"❌ Role `{role_name}` not found.")
        await member.remove_roles(role)
        embed = discord.Embed(
            title="Role Removed",
            description=f"Removed role `{role_name}` from {member.mention}.",
            color=discord.Color.orange()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def infractions(self, ctx, member: discord.Member):
        """View a user's warning/mute/kick/ban history."""
        # TODO: Implement infractions log
        await ctx.send(f"Infractions command for {member.mention} is not yet implemented.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def modlog(self, ctx):
        """Displays the mod log channel or actions."""
        # TODO: Implement modlog
        await ctx.send("Modlog command is not yet implemented.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def blacklist(self, ctx, member: discord.Member):
        """Blacklists a user from using commands."""
        # TODO: Implement blacklist
        await ctx.send(f"Blacklist command for {member.mention} is not yet implemented.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def whitelist(self, ctx, member: discord.Member):
        """Whitelists a user from moderation actions."""
        # TODO: Implement whitelist
        await ctx.send(f"Whitelist command for {member.mention} is not yet implemented.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def antiinvite(self, ctx, toggle: str):
        """Toggles anti-invite system."""
        # TODO: Implement antiinvite
        await ctx.send(f"Antiinvite command with toggle `{toggle}` is not yet implemented.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def antilink(self, ctx, toggle: str):
        """Blocks all non-whitelisted links."""
        # TODO: Implement antilink
        await ctx.send(f"Antilink command with toggle `{toggle}` is not yet implemented.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def antispam(self, ctx, toggle: str):
        """Enables automatic spam detection."""
        # TODO: Implement antispam
        await ctx.send(f"Antispam command with toggle `{toggle}` is not yet implemented.")

    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def antighostping(self, ctx, toggle: str):
        """Detects ghost pings and notifies staff."""
        # TODO: Implement antighostping
        await ctx.send(f"Antighostping command with toggle `{toggle}` is not yet implemented.")


    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def automod(self, ctx):
        """Opens interactive panel to configure auto moderation."""
        class AutomodPanel(ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.anti_invite = False
                self.anti_link = False
                self.anti_spam = False

            @ui.button(label="Toggle Anti-Invite", style=discord.ButtonStyle.primary, custom_id="anti_invite")
            async def toggle_invite(self, interaction: discord.Interaction, button: ui.Button):
                self.anti_invite = not self.anti_invite
                await interaction.response.edit_message(embed=self.make_embed(), view=self)

            @ui.button(label="Toggle Anti-Link", style=discord.ButtonStyle.primary, custom_id="anti_link")
            async def toggle_link(self, interaction: discord.Interaction, button: ui.Button):
                self.anti_link = not self.anti_link
                await interaction.response.edit_message(embed=self.make_embed(), view=self)

            @ui.button(label="Toggle Anti-Spam", style=discord.ButtonStyle.primary, custom_id="anti_spam")
            async def toggle_spam(self, interaction: discord.Interaction, button: ui.Button):
                self.anti_spam = not self.anti_spam
                await interaction.response.edit_message(embed=self.make_embed(), view=self)

            def make_embed(self):
                desc = (
                    f"**Anti-Invite:** {'🟢 Enabled' if self.anti_invite else '🔴 Disabled'}\n"
                    f"**Anti-Link:** {'🟢 Enabled' if self.anti_link else '🔴 Disabled'}\n"
                    f"**Anti-Spam:** {'🟢 Enabled' if self.anti_spam else '🔴 Disabled'}\n"
                )
                embed = discord.Embed(
                    title="Automod Panel",
                    description=desc,
                    color=discord.Color.blurple()
                )
                return embed

        view = AutomodPanel()
        embed = view.make_embed()
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
