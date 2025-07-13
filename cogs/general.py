
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
        is_guild_member = isinstance(member, discord.Member)
        display_name = member.display_name if is_guild_member else member.name
        mention = member.mention
        avatar_url = member.display_avatar.url if hasattr(member, 'display_avatar') else member.avatar.url if member.avatar else None

        # Dates
        joined = member.joined_at.strftime('%a, %b %d, %Y %I:%M %p') if is_guild_member and member.joined_at else "N/A"
        created = member.created_at.strftime('%a, %b %d, %Y %I:%M %p')

        # Roles
        roles = []
        if is_guild_member:
            roles = [role for role in member.roles if role.name != "@everyone"]
            roles_sorted = sorted(roles, key=lambda r: r.position, reverse=True)
            roles_display = " ".join([role.mention for role in roles_sorted[:10]])
            if len(roles_sorted) > 10:
                roles_display += f" and {len(roles_sorted)-10} more..."
            roles_field = f"{roles_display}" if roles_display else "None"
        else:
            roles_field = "N/A"

        # Permissions
        key_perms = []
        if is_guild_member:
            perms = member.guild_permissions
            perm_names = [
                ("Administrator", perms.administrator),
                ("Manage Server", perms.manage_guild),
                ("Manage Roles", perms.manage_roles),
                ("Manage Channels", perms.manage_channels),
                ("Manage Messages", perms.manage_messages),
                ("Manage Webhooks", perms.manage_webhooks),
                ("Manage Nicknames", perms.manage_nicknames),
                ("Manage Emojis and Stickers", perms.manage_emojis_and_stickers),
                ("Kick Members", perms.kick_members),
                ("Ban Members", perms.ban_members),
                ("Mention Everyone", perms.mention_everyone),
                ("Timeout Members", getattr(perms, 'moderate_members', False)),
            ]
            key_perms = [name for name, has in perm_names if has]
        perms_field = ", ".join(key_perms) if key_perms else "None"

        # Acknowledgements
        acknowledgements = []
        if is_guild_member:
            if member.guild.owner_id == member.id:
                acknowledgements.append("Server Owner")
            if member.guild_permissions.administrator:
                acknowledgements.append("Server Admin")
        if member.bot:
            acknowledgements.append("Bot")
        ack_field = ", ".join(acknowledgements) if acknowledgements else "None"

        # Build embed
        embed = discord.Embed(
            color=member.color if is_guild_member and member.color.value else discord.Color.blurple(),
            description=f"{mention}"
        )
        embed.set_author(name=display_name, icon_url=avatar_url)
        embed.set_thumbnail(url=avatar_url)
        embed.add_field(name="Joined", value=joined, inline=True)
        embed.add_field(name="Registered", value=created, inline=True)
        embed.add_field(name=f"Roles [{len(roles)}]", value=roles_field, inline=False)
        if perms_field != "None":
            embed.add_field(name="Key Permissions", value=perms_field, inline=False)
        if ack_field != "None":
            embed.add_field(name="Acknowledgements", value=ack_field, inline=False)
        embed.add_field(name="ID", value=f"`{member.id}`", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        # Show banner at bottom if available, else nothing
        if hasattr(member, 'banner') and member.banner:
            embed.set_image(url=member.banner.url)
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
            title=f"Info for {guild.name} ",
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
