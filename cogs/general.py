
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
        features = {
            "Server Discovery": "Server Discovery" in guild.features,
            "Invite Splash": "INVITE_SPLASH" in guild.features,
            "Vanity Invite": "VANITY_URL" in guild.features,
            "News Channels": "NEWS" in guild.features,
            "Animated Icon": "ANIMATED_ICON" in guild.features,
            "Banner": bool(guild.banner)
        }
        feature_text = "\n".join([
            f"{'✅' if v else '❌'} {k}" for k, v in features.items()
        ])

        # Channels
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        locked_text = len([c for c in guild.text_channels if c.overwrites_for(guild.default_role).read_messages is False])
        locked_voice = len([c for c in guild.voice_channels if c.overwrites_for(guild.default_role).connect is False])

        # Info
        scanning = "✅ Scanning Images" if "COMMUNITY" in guild.features else "❌ Scanning Images"
        verification = f"Verification level: {str(guild.verification_level)}"
        icon_link = f"[Icon link]({guild.icon.url})" if guild.icon else "No icon"

        # Prefixes (show all, or just main one)
        # Use bot's get_prefix function to get the current prefix for this guild
        prefix = None
        if hasattr(self.bot, 'command_prefix'):
            # command_prefix can be a function or a string
            if callable(self.bot.command_prefix):
                # Simulate a message object for get_prefix
                class Dummy:
                    def __init__(self, guild):
                        self.guild = guild
                        self.author = ctx.author
                prefixes = self.bot.command_prefix(self.bot, Dummy(guild))
                if isinstance(prefixes, (list, tuple)):
                    prefix = prefixes[0]
                else:
                    prefix = prefixes
            else:
                prefix = self.bot.command_prefix
        if not prefix:
            prefix = '!'
        prefix_display = f"`{prefix}`"

        # Members
        total = guild.member_count
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])

        # Roles
        roles = len(guild.roles)

        # Boosts
        boost_level = f"Level {guild.premium_tier} (maxed)" if guild.premium_tier == 3 else f"Level {guild.premium_tier}"

        embed = discord.Embed(
            title=f"Info for {guild.name} \U0001F338 • Lounge • Community • Vcs • Pfps\n• Banners • Active • Hangout !!",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        embed.add_field(name="Owner", value=guild.owner, inline=True)
        embed.add_field(name="Features", value=feature_text, inline=True)
        embed.add_field(name="Boosts", value=boost_level, inline=True)
        embed.add_field(name="Channels", value=f"# {text_channels} ({locked_text} locked)\n\U0001F50A {voice_channels} ({locked_voice} locked)", inline=True)
        embed.add_field(name="Info", value=f"{scanning}\n{verification}\n{icon_link}", inline=True)
        embed.add_field(name="Prefixes", value=prefix_display, inline=True)
        embed.add_field(name="Members", value=f"Total: {total}\nHumans: {humans}\nBots: {bots}", inline=True)
        embed.add_field(name="Roles", value=f"{roles} roles", inline=True)
        embed.add_field(name="ID", value=guild.id, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:f>", inline=True)
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
