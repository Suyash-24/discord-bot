import discord
from discord.ext import commands
from discord import app_commands
from discord.utils import get

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Kick
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f"👢 Kicked {member.mention} | Reason: {reason}")

    # Ban
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f"🔨 Banned {member.mention} | Reason: {reason}")

    # Unban
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, *, user):
        banned_users = await ctx.guild.bans()
        name, discriminator = user.split("#")
        for ban_entry in banned_users:
            if (ban_entry.user.name, ban_entry.user.discriminator) == (name, discriminator):
                await ctx.guild.unban(ban_entry.user)
                await ctx.send(f"✅ Unbanned {ban_entry.user.mention}")
                return
        await ctx.send("❌ User not found in ban list.")

    # Clear
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"🧹 Cleared {amount} messages", delete_after=3)

    # Mute
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        role = get(ctx.guild.roles, name="Muted")
        if not role:
            role = await ctx.guild.create_role(name="Muted")
            for channel in ctx.guild.channels:
                await channel.set_permissions(role, speak=False, send_messages=False, read_message_history=True)
        await member.add_roles(role, reason=reason)
        await ctx.send(f"🔇 Muted {member.mention} | Reason: {reason}")

    # Unmute
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        role = get(ctx.guild.roles, name="Muted")
        if role in member.roles:
            await member.remove_roles(role)
            await ctx.send(f"🔊 Unmuted {member.mention}")
        else:
            await ctx.send("❌ User is not muted.")

    # Lock Channel
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Channel locked.")

    # Unlock Channel
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Channel unlocked.")

    # Set Slowmode
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"🐢 Slowmode set to {seconds} seconds.")

    # Timeout
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, seconds: int, *, reason=None):
        duration = discord.utils.utcnow() + discord.timedelta(seconds=seconds)
        await member.timeout(until=duration, reason=reason)
        await ctx.send(f"⏳ {member.mention} has been timed out for {seconds} seconds.")

    # Untimeout
    @commands.command()
    @commands.has_permissions(moderate_members=True)
    async def untimeout(self, ctx, member: discord.Member):
        await member.timeout(until=None)
        await ctx.send(f"✅ {member.mention}'s timeout has been removed.")

    # Change Nickname
    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def nickname(self, ctx, member: discord.Member, *, nickname: str = None):
        await member.edit(nick=nickname)
        await ctx.send(f"✏️ Nickname changed to `{nickname}` for {member.mention}")

    # Add Role
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def roleadd(self, ctx, member: discord.Member, *, role: discord.Role):
        await member.add_roles(role)
        await ctx.send(f"✅ Added {role.name} to {member.mention}")

    # Remove Role
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def roleremove(self, ctx, member: discord.Member, *, role: discord.Role):
        await member.remove_roles(role)
        await ctx.send(f"❌ Removed {role.name} from {member.mention}")

    # Softban
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member: discord.Member, *, reason=None):
        await ctx.guild.ban(member, reason=reason)
        await ctx.guild.unban(member)
        await ctx.send(f"🧼 Softbanned {member.mention}")

    # Warn (basic)
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        await ctx.send(f"⚠️ {member.mention} has been warned. Reason: {reason}")

async def setup(bot):
    await bot.add_cog(Moderation(bot))
