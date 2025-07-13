
import discord
from discord.ext import commands
from typing import Optional

class General(commands.Cog):
    """General commands for everyone."""
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def about(self, ctx):
        """Show info about the bot."""
        embed = discord.Embed(
            title="About the Bot",
            description="A multipurpose Discord bot for moderation, fun, and more!",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    async def userinfo(self, ctx, member: Optional[discord.Member] = None):
        """Show info about a user."""
        member = member or ctx.author
        embed = discord.Embed(
            title=f"User Info - {member}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url if hasattr(member, 'display_avatar') else member.avatar.url if member.avatar else None)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Joined", value=member.joined_at.strftime('%Y-%m-%d %H:%M:%S') if member.joined_at else "N/A")
        embed.add_field(name="Account Created", value=member.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command()
    async def serverinfo(self, ctx):
        """Show info about the server."""
        guild = ctx.guild
        embed = discord.Embed(
            title=f"Server Info - {guild.name}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="ID", value=guild.id)
        embed.add_field(name="Owner", value=guild.owner)
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Created At", value=guild.created_at.strftime('%Y-%m-%d %H:%M:%S'))
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command(aliases=["av", "pfp"])
    async def avatar(self, ctx, member: Optional[discord.Member] = None):
        """Show a user's avatar."""
        member = member or ctx.author
        embed = discord.Embed(
            title=f"Avatar - {member}",
            color=discord.Color.purple()
        )
        embed.set_image(url=member.display_avatar.url if hasattr(member, 'display_avatar') else member.avatar.url if member.avatar else None)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
