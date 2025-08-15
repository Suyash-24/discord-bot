import discord
import typing
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Optional

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------------------- PING --------------------
    @commands.command(name="ping")
    async def ping_command(self, ctx):
        """Shows bot latency (prefix version)"""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: `{latency}ms`",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @app_commands.command(name="ping", description="Shows bot latency")
    async def ping_slash(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Latency: `{latency}ms`",
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------------------- SERVER INFO --------------------
    @commands.command(name="serverinfo")
    async def serverinfo_command(self, ctx):
        """Shows detailed information about the current server (prefix version)"""
        guild = ctx.guild
        if not guild:
            await ctx.send("This command can only be used in a server.")
            return
        owner = guild.owner
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        categories = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        threads = len(guild.threads)
        emojis = len(guild.emojis)
        stickers = len(getattr(guild, 'stickers', []))
        features = guild.features
        roles = len(guild.roles)
        boost_level = guild.premium_tier
        boosts = guild.premium_subscription_count
        booster_role = discord.utils.get(guild.roles, name="Booster")
        created_at = guild.created_at.strftime("%A, %B %d, %Y %I:%M %p")
        # About Section
        about = (
            f"**Server Name:** {guild.name}\n"
            f"**Server ID:** {guild.id}\n"
            f"**Owner :** {owner.mention if owner else 'Unknown'}\n"
            f"**Created At:** {created_at}\n"
            f"**Members:** {guild.member_count}\n"
            f"**Roles:** {roles}\n"
            f"**Verification Level:** {guild.verification_level.name.title()}\n"
        )
        # Description
        description = guild.description or "Welcome to {0}".format(guild.name)
        # Features
        feature_map = {
            "GUILD_ONBOARDING": "Guild Onboarding",
            "INVITE_SPLASH": "Invite Splash",
            "VIP_REGIONS": "VIP Regions",
            "VANITY_URL": "Vanity URL",
            "ANIMATED_ICON": "Animated Icon",
            "DISCOVERABLE": "Discoverable",
            "PREVIEW_ENABLED": "Preview Enabled",
            "COMMUNITY": "Community",
            "BANNER": "Banner",
            "TIER_1": "Tier 1 Boost",
            "TIER_2": "Tier 2 Boost",
            "TIER_3": "Tier 3 Boost",
            "NEWS": "News Channels",
            "PARTNERED": "Partnered",
            "COMMERCE": "Commerce",
            "ENABLED_DISCOVERABLE_BEFORE": "Enabled Discoverable Before",
            "GUILD_ONBOARDING_HAS_PROMPTS": "Guild Onboarding Has Prompts",
            "AUTO_MODERATION": "Auto Moderation",
            "MORE_EMOJI": "More Emojis",
            "MORE_STICKERS": "More Stickers",
            "TIER_1": "Tier 1 Boost",
            "TIER_2": "Tier 2 Boost",
            "TIER_3": "Tier 3 Boost",
            "TIER_4": "Tier 4 Boost",
            "TIER_5": "Tier 5 Boost",
            "TIER_6": "Tier 6 Boost",
            "TIER_7": "Tier 7 Boost",
            "TIER_8": "Tier 8 Boost",
            "TIER_9": "Tier 9 Boost",
            "TIER_10": "Tier 10 Boost",
        }
        features_list = [f"✅ {feature_map.get(f, f.replace('_', ' ').title())}" for f in features]
        features_str = "\n".join(features_list) if features_list else "No special features."
        # Members/Channels/Emojis/Boosts
        member_info = f"**Members:** {guild.member_count}\n**Humans:** {humans}\n**Bots:** {bots}"
        channel_info = f"**Categories:** {categories}\n**Text Channels:** {text_channels}\n**Voice Channels:** {voice_channels}\n**Threads:** {threads}"
        emoji_info = f"**Regular Emojis:** {emojis}\n**Stickers:** {stickers}\n**Total Emoji/Stickers:** {emojis + stickers}"
        boost_info = f"**Level:** {boost_level} [ {boosts} Boosts ]\n**Booster Role:** {booster_role.mention if booster_role else 'N/A'}"
        # Build Embeds (split for Discord limits)
        embeds = []
        # About/Description/Features
        embed1 = discord.Embed(title=f"{guild.name} • Information", color=discord.Color.blurple(), timestamp=datetime.utcnow())
        embed1.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed1.add_field(name="About(s)", value=about, inline=False)
        embed1.add_field(name="Description(s)", value=description, inline=False)
        embed1.add_field(name="Feature(s)", value=features_str, inline=False)
        embeds.append(embed1)
        # Members/Channels/Emojis/Boosts
        embed2 = discord.Embed(title=f"{guild.name} • Stats", color=discord.Color.blurple(), timestamp=datetime.utcnow())
        embed2.add_field(name="Member(s)", value=member_info, inline=False)
        embed2.add_field(name="Channel(s)", value=channel_info, inline=False)
        embed2.add_field(name="Emoji Info(s)", value=emoji_info, inline=False)
        embed2.add_field(name="Boost Status(s)", value=boost_info, inline=False)
        embeds.append(embed2)
        # Server Banner/Image
        if guild.banner:
            embed3 = discord.Embed(title=f"{guild.name} • Banner", color=discord.Color.blurple(), timestamp=datetime.utcnow())
            embed3.set_image(url=guild.banner.url)
            embeds.append(embed3)
        # Send all embeds
        for i, em in enumerate(embeds):
            await ctx.send(embed=em)

    @app_commands.command(name="serverinfo", description="Shows information about the server")
    async def serverinfo_slash(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
        owner = guild.owner
        humans = len([m for m in guild.members if not m.bot])
        bots = len([m for m in guild.members if m.bot])
        categories = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        threads = len(guild.threads)
        emojis = len(guild.emojis)
        stickers = len(getattr(guild, 'stickers', []))
        features = guild.features
        roles = len(guild.roles)
        boost_level = guild.premium_tier
        boosts = guild.premium_subscription_count
        booster_role = discord.utils.get(guild.roles, name="Booster")
        created_at = guild.created_at.strftime("%A, %B %d, %Y %I:%M %p")
        about = (
            f"**Server Name:** {guild.name}\n"
            f"**Server ID:** {guild.id}\n"
            f"**Owner :** {owner.mention if owner else 'Unknown'}\n"
            f"**Created At:** {created_at}\n"
            f"**Members:** {guild.member_count}\n"
            f"**Roles:** {roles}\n"
            f"**Verification Level:** {guild.verification_level.name.title()}\n"
        )
        description = guild.description or "Welcome to {0}".format(guild.name)
        feature_map = {
            "GUILD_ONBOARDING": "Guild Onboarding",
            "INVITE_SPLASH": "Invite Splash",
            "VIP_REGIONS": "VIP Regions",
            "VANITY_URL": "Vanity URL",
            "ANIMATED_ICON": "Animated Icon",
            "DISCOVERABLE": "Discoverable",
            "PREVIEW_ENABLED": "Preview Enabled",
            "COMMUNITY": "Community",
            "BANNER": "Banner",
            "TIER_1": "Tier 1 Boost",
            "TIER_2": "Tier 2 Boost",
            "TIER_3": "Tier 3 Boost",
            "NEWS": "News Channels",
            "PARTNERED": "Partnered",
            "COMMERCE": "Commerce",
            "ENABLED_DISCOVERABLE_BEFORE": "Enabled Discoverable Before",
            "GUILD_ONBOARDING_HAS_PROMPTS": "Guild Onboarding Has Prompts",
            "AUTO_MODERATION": "Auto Moderation",
            "MORE_EMOJI": "More Emojis",
            "MORE_STICKERS": "More Stickers",
            "TIER_1": "Tier 1 Boost",
            "TIER_2": "Tier 2 Boost",
            "TIER_3": "Tier 3 Boost",
            "TIER_4": "Tier 4 Boost",
            "TIER_5": "Tier 5 Boost",
            "TIER_6": "Tier 6 Boost",
            "TIER_7": "Tier 7 Boost",
            "TIER_8": "Tier 8 Boost",
            "TIER_9": "Tier 9 Boost",
            "TIER_10": "Tier 10 Boost",
        }
        features_list = [f"✅ {feature_map.get(f, f.replace('_', ' ').title())}" for f in features]
        features_str = "\n".join(features_list) if features_list else "No special features."
        member_info = f"**Members:** {guild.member_count}\n**Humans:** {humans}\n**Bots:** {bots}"
        channel_info = f"**Categories:** {categories}\n**Text Channels:** {text_channels}\n**Voice Channels:** {voice_channels}\n**Threads:** {threads}"
        emoji_info = f"**Regular Emojis:** {emojis}\n**Stickers:** {stickers}\n**Total Emoji/Stickers:** {emojis + stickers}"
        boost_info = f"**Level:** {boost_level} [ {boosts} Boosts ]\n**Booster Role:** {booster_role.mention if booster_role else 'N/A'}"
        embeds = []
        embed1 = discord.Embed(title=f"{guild.name} • Information", color=discord.Color.blurple(), timestamp=datetime.utcnow())
        embed1.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed1.add_field(name="About(s)", value=about, inline=False)
        embed1.add_field(name="Description(s)", value=description, inline=False)
        embed1.add_field(name="Feature(s)", value=features_str, inline=False)
        embeds.append(embed1)
        embed2 = discord.Embed(title=f"{guild.name} • Stats", color=discord.Color.blurple(), timestamp=datetime.utcnow())
        embed2.add_field(name="Member(s)", value=member_info, inline=False)
        embed2.add_field(name="Channel(s)", value=channel_info, inline=False)
        embed2.add_field(name="Emoji Info(s)", value=emoji_info, inline=False)
        embed2.add_field(name="Boost Status(s)", value=boost_info, inline=False)
        embeds.append(embed2)
        if guild.banner:
            embed3 = discord.Embed(title=f"{guild.name} • Banner", color=discord.Color.blurple(), timestamp=datetime.utcnow())
            embed3.set_image(url=guild.banner.url)
            embeds.append(embed3)
        # Send all embeds as a followup (ephemeral)
        await interaction.response.send_message(embed=embeds[0], ephemeral=True)
        for em in embeds[1:]:
            await interaction.followup.send(embed=em, ephemeral=True)

    # -------------------- USER INFO --------------------
    @commands.command(name="userinfo")
    async def userinfo_command(self, ctx, member: Optional[discord.Member] = None):
        """Shows information about a user (prefix version)"""
        member = member or ctx.author
        if not member:
            await ctx.send("User not found.")
            return
        embed = discord.Embed(
            title=f"👤 User Info - {member}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow(),
            description=f"Info for {member.mention}"
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
        embed.add_field(name="🆔 ID", value=member.id, inline=True)
        joined_at = "N/A"
        if getattr(member, 'joined_at', None) is not None and member.joined_at:
            try:
                joined_at = member.joined_at.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                joined_at = "N/A"
        embed.add_field(name="📥 Joined Server", value=joined_at, inline=True)
        embed.add_field(name="📆 Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="🎭 Roles", value=", ".join([role.mention for role in member.roles[1:]]) or "None", inline=False)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        @commands.command(name="userinfo")
        async def userinfo_command(self, ctx, member: Optional[typing.Union[discord.Member, str, int]] = None):
            """Shows information about a user (prefix version). Accepts mention, member, or user ID."""
            resolved = None
            if member is None:
                resolved = ctx.author
            elif isinstance(member, discord.Member):
                resolved = member
            else:
                try:
                    member_id = int(member)
                    resolved = ctx.guild.get_member(member_id) or await self.bot.fetch_user(member_id)
                except Exception:
                    await ctx.send("❌ Could not find a user with that ID.")
                    return
            if not resolved:
                await ctx.send("❌ Could not resolve user.")
                return
            embed = discord.Embed(
                title=f"👤 User Info - {resolved}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow(),
                description=f"Info for {getattr(resolved, 'mention', str(resolved))}"
            )
            avatar_url = resolved.avatar.url if hasattr(resolved, 'avatar') and resolved.avatar else None
            embed.set_thumbnail(url=avatar_url)
            embed.add_field(name="🆔 ID", value=resolved.id, inline=True)
            if isinstance(resolved, discord.Member):
                joined_at = "N/A"
                if resolved.joined_at:
                    try:
                        joined_at = resolved.joined_at.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        joined_at = "N/A"
                embed.add_field(name="📥 Joined Server", value=joined_at, inline=True)
                embed.add_field(name="🎭 Roles", value=", ".join([role.mention for role in resolved.roles[1:]]) or "None", inline=False)
                embed.add_field(name="📆 Account Created", value=resolved.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
            else:
                # Only show account creation date for non-Member (User)
                if hasattr(resolved, 'created_at'):
                    embed.add_field(name="📆 Account Created", value=resolved.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

    @app_commands.command(name="userinfo", description="Shows information about a user")
    @app_commands.describe(member="The user to get information about")
    async def userinfo_slash(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        resolved_member = member or (interaction.user if isinstance(interaction.user, discord.Member) else None)
        if not resolved_member:
            return await interaction.response.send_message("User not found.", ephemeral=True)
        embed = discord.Embed(
            title=f"👤 User Info - {resolved_member}",
            color=discord.Color.green(),
            timestamp=datetime.utcnow(),
            description=f"Info for {resolved_member.mention}"
        )
        embed.set_thumbnail(url=resolved_member.avatar.url if resolved_member.avatar else None)
        embed.add_field(name="🆔 ID", value=resolved_member.id, inline=True)
        joined_at = "N/A"
        if getattr(resolved_member, 'joined_at', None) is not None and resolved_member.joined_at:
            try:
                joined_at = resolved_member.joined_at.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                joined_at = "N/A"
        embed.add_field(name="📥 Joined Server", value=joined_at, inline=True)
        embed.add_field(name="📆 Account Created", value=resolved_member.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
        embed.add_field(name="🎭 Roles", value=", ".join([role.mention for role in resolved_member.roles[1:]]) or "None", inline=False)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        @app_commands.command(name="userinfo", description="Shows information about a user")
        @app_commands.describe(member="The user to get information about (mention, user, or user ID)")
        async def userinfo_slash(self, interaction: discord.Interaction, member: Optional[discord.User] = None, user_id: Optional[str] = None):
            resolved = None
            if member is not None:
                resolved = member
            elif user_id is not None:
                try:
                    resolved = await self.bot.fetch_user(int(user_id))
                except Exception:
                    return await interaction.response.send_message("❌ Could not find a user with that ID.", ephemeral=True)
            else:
                resolved = interaction.user
            if not resolved:
                return await interaction.response.send_message("❌ Could not resolve user.", ephemeral=True)
            embed = discord.Embed(
                title=f"👤 User Info - {resolved}",
                color=discord.Color.green(),
                timestamp=datetime.utcnow(),
                description=f"Info for {getattr(resolved, 'mention', str(resolved))}"
            )
            avatar_url = resolved.avatar.url if hasattr(resolved, 'avatar') and resolved.avatar else None
            embed.set_thumbnail(url=avatar_url)
            embed.add_field(name="🆔 ID", value=resolved.id, inline=True)
            if isinstance(resolved, discord.Member):
                joined_at = "N/A"
                if resolved.joined_at:
                    try:
                        joined_at = resolved.joined_at.strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        joined_at = "N/A"
                embed.add_field(name="📥 Joined Server", value=joined_at, inline=True)
                embed.add_field(name="📆 Account Created", value=resolved.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
                embed.add_field(name="🎭 Roles", value=", ".join([role.mention for role in resolved.roles[1:]]) or "None", inline=False)
            else:
                embed.add_field(name="📆 Account Created", value=resolved.created_at.strftime("%Y-%m-%d %H:%M:%S"), inline=True)
            embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------------------- AVATAR --------------------
    @commands.command(name="avatar")
    async def avatar_command(self, ctx, member: Optional[discord.Member] = None):
        """Shows a user's avatar (prefix version)"""
        member = member or ctx.author
        embed = discord.Embed(
            title=f"🖼️ Avatar for {member}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_image(url=member.avatar.url if member.avatar else None)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)
        @commands.command(name="avatar")
        async def avatar_command(self, ctx, member: Optional[typing.Union[discord.Member, str, int]] = None):
            """Shows a user's avatar (prefix version). Accepts mention, member, or user ID."""
            user = None
            if member is None:
                user = ctx.author
            elif isinstance(member, discord.Member):
                user = member
            else:
                try:
                    member_id = int(member)
                    user = ctx.guild.get_member(member_id) or await self.bot.fetch_user(member_id)
                except Exception:
                    await ctx.send("❌ Could not find a user with that ID.")
                    return
            if not user:
                await ctx.send("❌ Could not resolve user.")
                return
            user = await self.bot.fetch_user(user.id)
            embed = discord.Embed(
                title=f"🖼️ Avatar for {user}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.set_image(url=user.avatar.url if user.avatar else user.display_avatar.url)
            embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
            await ctx.send(embed=embed)

    @app_commands.command(name="avatar", description="Shows a user's avatar")
    @app_commands.describe(member="The user to get the avatar of")
    async def avatar_slash(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        resolved_member = member or (interaction.user if isinstance(interaction.user, discord.Member) else None)
        if not resolved_member:
            return await interaction.response.send_message("User not found.", ephemeral=True)
        embed = discord.Embed(
            title=f"🖼️ Avatar for {resolved_member}",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_image(url=resolved_member.avatar.url if resolved_member.avatar else None)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        @app_commands.command(name="avatar", description="Shows a user's avatar")
        @app_commands.describe(member="The user to get the avatar of (mention, user, or user ID)")
        async def avatar_slash(self, interaction: discord.Interaction, member: Optional[discord.User] = None, user_id: Optional[str] = None):
            user = None
            if member is not None:
                user = member
            elif user_id is not None:
                try:
                    user = await self.bot.fetch_user(int(user_id))
                except Exception:
                    await interaction.response.send_message("❌ Could not find a user with that ID.", ephemeral=True)
                    return
            else:
                user = interaction.user
            if not user:
                await interaction.response.send_message("❌ Could not resolve user.", ephemeral=True)
                return
            user = await self.bot.fetch_user(user.id)
            embed = discord.Embed(
                title=f"🖼️ Avatar for {user}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.set_image(url=user.avatar.url if user.avatar else user.display_avatar.url)
            embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------------------- BANNER --------------------
    @commands.command(name="banner")
    async def banner_command(self, ctx, member: Optional[typing.Union[discord.Member, str, int]] = None):
        """Shows a user's banner (prefix version). Accepts mention, member, or user ID."""
        user = None
        if member is None:
            user = ctx.author
        elif isinstance(member, discord.Member):
            user = member
        else:
            # Try to resolve as user ID
            try:
                member_id = int(member)
                user = await self.bot.fetch_user(member_id)
            except Exception:
                await ctx.send("❌ Could not find a user with that ID.")
                return
        if not user:
            await ctx.send("❌ Could not resolve user.")
            return
        user = await self.bot.fetch_user(user.id)
        embed = discord.Embed(
            title=f"🎫 Banner for {user}",
            color=discord.Color.teal(),
            timestamp=datetime.utcnow()
        )
        if user.banner:
            embed.set_image(url=user.banner.url)
        else:
            embed.description = "No banner found."
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @app_commands.command(name="banner", description="Shows a user's banner")
    @app_commands.describe(member="The user to get the banner of (mention, user, or user ID)")
    async def banner_slash(self, interaction: discord.Interaction, member: Optional[discord.User] = None, user_id: Optional[str] = None):
        user = None
        if member is not None:
            user = member
        elif user_id is not None:
            try:
                user = await self.bot.fetch_user(int(user_id))
            except Exception:
                await interaction.response.send_message("❌ Could not find a user with that ID.", ephemeral=True)
                return
        else:
            user = interaction.user
        if not user:
            await interaction.response.send_message("❌ Could not resolve user.", ephemeral=True)
            return
        user = await self.bot.fetch_user(user.id)
        embed = discord.Embed(
            title=f"🎫 Banner for {user}",
            color=discord.Color.teal(),
            timestamp=datetime.utcnow()
        )
        if user.banner:
            embed.set_image(url=user.banner.url)
        else:
            embed.description = "No banner found."
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------------------- ABOUT --------------------
    @commands.command(name="about")
    async def about_command(self, ctx):
        """Shows info about the bot (prefix version)"""
        embed = discord.Embed(
            title="🤖 About This Bot",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow(),
            description="A multipurpose Discord bot with moderation, utility, and fun features!"
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user else None)
        embed.add_field(name="👤 Creator", value="Your Name", inline=True)
        embed.add_field(name="📚 Library", value="discord.py", inline=True)
        embed.add_field(name="🌐 Servers", value=len(self.bot.guilds), inline=True)
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @app_commands.command(name="about", description="Shows info about the bot")
    async def about_slash(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 About This Bot",
            color=discord.Color.purple(),
            timestamp=datetime.utcnow(),
            description="A multipurpose Discord bot with moderation, utility, and fun features!"
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url if self.bot.user else None)
        embed.add_field(name="👤 Creator", value="Your Name", inline=True)
        embed.add_field(name="📚 Library", value="discord.py", inline=True)
        embed.add_field(name="🌐 Servers", value=len(self.bot.guilds), inline=True)
        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(General(bot))
