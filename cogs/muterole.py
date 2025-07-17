import discord
from discord.ext import commands

class MuteRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_mute_role(self, guild: discord.Guild) -> discord.Role:
        """Ensure the muted role exists, if not, create and configure it."""
        muted_role = discord.utils.get(guild.roles, name="Muted")

        if not muted_role:
            muted_role = await guild.create_role(name="Muted", reason="To mute users")

            # Remove send permissions in all text channels
            for channel in guild.text_channels:
                await channel.set_permissions(muted_role, send_messages=False, add_reactions=False)

        return muted_role

    @commands.command(name="mute")
    @commands.has_permissions(manage_roles=True)
    async def mute(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Mute a member by adding the Muted role."""
        muted_role = await self.ensure_mute_role(ctx.guild)

        if muted_role in member.roles:
            return await ctx.send(f"{member.mention} is already muted!")

        await member.add_roles(muted_role, reason=reason)
        await ctx.send(f"🔇 Muted {member.mention} | Reason: `{reason}`")

    @commands.command(name="unmute")
    @commands.has_permissions(manage_roles=True)
    async def unmute(self, ctx, member: discord.Member):
        """Unmute a member by removing the Muted role."""
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")

        if not muted_role or muted_role not in member.roles:
            return await ctx.send(f"{member.mention} is not muted!")

        await member.remove_roles(muted_role)
        await ctx.send(f"🔊 Unmuted {member.mention}")

    @mute.error
    @unmute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please mention a user to mute/unmute.")
        else:
            await ctx.send(f"An error occurred: `{str(error)}`")

async def setup(bot):
    await bot.add_cog(MuteRole(bot))
