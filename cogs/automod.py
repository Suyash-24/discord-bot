import discord
from discord.ext import commands
from discord import ui

class Automod(commands.Cog):
    async def on_message(self, message):
        if not message.guild or message.author.bot:
            return
        guild_id = message.guild.id
        config = self.get_guild_config(guild_id)
        member = message.author
        triggered_features = []

        # Helper functions
        async def do_warn(feature):
            try:
                await message.channel.send(f"{member.mention}, you triggered automod: **{feature.replace('_',' ').title()}**.", delete_after=8)
            except Exception:
                pass

        async def do_mute(feature):
            # Try to find mute role
            mute_role = discord.utils.get(message.guild.roles, name="Muted")
            if not mute_role:
                embed = discord.Embed(
                    title="Mute Role Not Found",
                    description="No mute role named 'Muted' found. Please set up a mute role for automod to work.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Requested by {message.author.display_name}", icon_url=message.author.display_avatar.url if hasattr(message.author, 'display_avatar') else message.author.avatar.url if message.author.avatar else None)
                await message.channel.send(embed=embed)
                return
            if mute_role not in member.roles:
                try:
                    await member.add_roles(mute_role, reason=f"Automod mute ({feature})")
                    embed = discord.Embed(
                        title="User Muted",
                        description=f"{member.mention} has been muted for **{feature.replace('_',' ').title()}**.",
                        color=discord.Color.blurple()
                    )
                    embed.set_footer(text=f"Requested by {message.author.display_name}", icon_url=message.author.display_avatar.url if hasattr(message.author, 'display_avatar') else message.author.avatar.url if message.author.avatar else None)
                    await message.channel.send(embed=embed)
                except Exception:
                    embed = discord.Embed(
                        title="Mute Failed",
                        description=f"Failed to mute {member.mention} for **{feature.replace('_',' ').title()}**.",
                        color=discord.Color.red()
                    )
                    embed.set_footer(text=f"Requested by {message.author.display_name}", icon_url=message.author.display_avatar.url if hasattr(message.author, 'display_avatar') else message.author.avatar.url if message.author.avatar else None)
                    await message.channel.send(embed=embed)

        # Feature checks
        content = message.content
        # antiinvite
        if config.get('antiinvite', {}).get('delete') and ("discord.gg/" in content or "discord.com/invite/" in content):
            triggered_features.append('antiinvite')
        # antilink
        if config.get('antilink', {}).get('delete') and ("http://" in content or "https://" in content):
            triggered_features.append('antilink')
        # antispam (simple: repeated chars or words)
        if config.get('antispam', {}).get('delete') and (len(content) > 200 or any(content.count(w) > 5 for w in content.split())):
            triggered_features.append('antispam')
        # antimention (mass mention)
        if config.get('antimention', {}).get('delete') and (len(message.mentions) >= 5):
            triggered_features.append('antimention')
        # antighostping (mention then delete)
        # This needs message delete tracking, so skip for now
        # antitoken (discord token regex)
        import re
        token_regex = r"[MN][A-Za-z\d]{23}\.[\w-]{6}\.[\w-]{27}"
        if config.get('antitoken', {}).get('delete') and re.search(token_regex, content):
            triggered_features.append('antitoken')
        # antinsfw (simple: nsfw words)
        nsfw_words = ["porn", "sex", "nude", "boobs", "nsfw"]
        if config.get('antinsfw', {}).get('delete') and any(w in content.lower() for w in nsfw_words):
            triggered_features.append('antinsfw')
        # antiattachment (block files)
        if config.get('antiattachment', {}).get('delete') and message.attachments:
            triggered_features.append('antiattachment')
        # antiemoji (block excessive emojis)
        emoji_count = sum(1 for c in content if c in [chr(i) for i in range(0x1F600, 0x1F64F)])
        if config.get('antiemoji', {}).get('delete') and emoji_count > 5:
            triggered_features.append('antiemoji')
        # antizalgo (zalgo text)
        zalgo_chars = [chr(i) for i in range(0x0300, 0x036F)]
        if config.get('antizalgo', {}).get('delete') and any(c in zalgo_chars for c in content):
            triggered_features.append('antizalgo')
        # antidupe (duplicate messages)
        # Needs message history, skip for now
        # antiwords (custom block words)
        block_words = ["badword1", "badword2"] # You can make this configurable
        if config.get('antiwords', {}).get('delete') and any(w in content.lower() for w in block_words):
            triggered_features.append('antiwords')
        # anticaps (excessive caps)
        if config.get('anticaps', {}).get('delete') and sum(1 for c in content if c.isupper()) > 30:
            triggered_features.append('anticaps')
        # antiunicode (excessive unicode)
        if config.get('antiunicode', {}).get('delete') and sum(1 for c in content if ord(c) > 1000) > 10:
            triggered_features.append('antiunicode')
        # antiservers (server invite)
        if config.get('antiservers', {}).get('delete') and ("discord.gg/" in content or "discord.com/invite/" in content):
            triggered_features.append('antiservers')
        # antiurl (any url)
        url_regex = r"https?://[\w.-]+"
        if config.get('antiurl', {}).get('delete') and re.search(url_regex, content):
            triggered_features.append('antiurl')

        # Apply actions for each triggered feature
        for feature in triggered_features:
            actions = config.get(feature, {})
            if actions.get('delete'):
                try:
                    await message.delete()
                except Exception:
                    pass
            if actions.get('warn'):
                await do_warn(feature)
            if actions.get('mute'):
                await do_mute(feature)

    # In-memory config: {guild_id: {feature: {'delete': bool, 'warn': bool, 'mute': bool}}}
    automod_config = {}

    def get_guild_config(self, guild_id):
        if guild_id not in self.automod_config:
            self.automod_config[guild_id] = {}
        return self.automod_config[guild_id]

    def set_feature_action(self, guild_id, feature, action, value):
        config = self.get_guild_config(guild_id)
        if feature not in config:
            config[feature] = {'delete': False, 'warn': False, 'mute': False}
        config[feature][action] = value

    def get_feature_actions(self, guild_id, feature):
        config = self.get_guild_config(guild_id)
        return config.get(feature, {'delete': False, 'warn': False, 'mute': False})

    def make_status_embed(self, ctx, feature, actions):
        desc = (
            f"**Delete Message:** {'🟢 Enabled' if actions['delete'] else '🔴 Disabled'}\n"
            f"**Warn User:** {'🟢 Enabled' if actions['warn'] else '🔴 Disabled'}\n"
            f"**Mute User:** {'🟢 Enabled' if actions['mute'] else '🔴 Disabled'}\n"
        )
        embed = discord.Embed(
            title=f"Automod: {feature.replace('_',' ').title()} Settings",
            description=desc,
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        return embed

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def antiinvite(self, ctx):
        """Show or configure anti-invite actions."""
        actions = self.get_feature_actions(ctx.guild.id, 'antiinvite')
        embed = self.make_status_embed(ctx, 'antiinvite', actions)
        await ctx.send(embed=embed)

    @antiinvite.command(name="delete")
    @commands.has_permissions(manage_guild=True)
    async def delete_antiinvite(self, ctx, on_off: str):
        """Enable/disable message deletion for invite links."""
        value = on_off.lower() == 'on'
        self.set_feature_action(ctx.guild.id, 'antiinvite', 'delete', value)
        actions = self.get_feature_actions(ctx.guild.id, 'antiinvite')
        embed = self.make_status_embed(ctx, 'antiinvite', actions)
        await ctx.send(embed=embed)

    @antiinvite.command(name="warn")
    @commands.has_permissions(manage_guild=True)
    async def warn_antiinvite(self, ctx, on_off: str):
        """Enable/disable warning for invite links."""
        value = on_off.lower() == 'on'
        self.set_feature_action(ctx.guild.id, 'antiinvite', 'warn', value)
        actions = self.get_feature_actions(ctx.guild.id, 'antiinvite')
        embed = self.make_status_embed(ctx, 'antiinvite', actions)
        await ctx.send(embed=embed)

    @antiinvite.command(name="mute")
    @commands.has_permissions(manage_guild=True)
    async def mute_antiinvite(self, ctx, on_off: str):
        """Enable/disable muting for invite links."""
        value = on_off.lower() == 'on'
        self.set_feature_action(ctx.guild.id, 'antiinvite', 'mute', value)
        actions = self.get_feature_actions(ctx.guild.id, 'antiinvite')
        embed = self.make_status_embed(ctx, 'antiinvite', actions)
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def antilink(self, ctx):
        """Show or configure anti-link actions."""
        actions = self.get_feature_actions(ctx.guild.id, 'antilink')
        embed = self.make_status_embed(ctx, 'antilink', actions)
        await ctx.send(embed=embed)

    @antilink.command(name="delete")
    @commands.has_permissions(manage_guild=True)
    async def delete_antilink(self, ctx, on_off: str):
        value = on_off.lower() == 'on'
        self.set_feature_action(ctx.guild.id, 'antilink', 'delete', value)
        actions = self.get_feature_actions(ctx.guild.id, 'antilink')
        embed = self.make_status_embed(ctx, 'antilink', actions)
        await ctx.send(embed=embed)

    @antilink.command(name="warn")
    @commands.has_permissions(manage_guild=True)
    async def warn_antilink(self, ctx, on_off: str):
        value = on_off.lower() == 'on'
        self.set_feature_action(ctx.guild.id, 'antilink', 'warn', value)
        actions = self.get_feature_actions(ctx.guild.id, 'antilink')
        embed = self.make_status_embed(ctx, 'antilink', actions)
        await ctx.send(embed=embed)

    @antilink.command(name="mute")
    @commands.has_permissions(manage_guild=True)
    async def mute_antilink(self, ctx, on_off: str):
        value = on_off.lower() == 'on'
        self.set_feature_action(ctx.guild.id, 'antilink', 'mute', value)
        actions = self.get_feature_actions(ctx.guild.id, 'antilink')
        embed = self.make_status_embed(ctx, 'antilink', actions)
        await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def antispam(self, ctx):
        """Show or configure anti-spam actions."""
        actions = self.get_feature_actions(ctx.guild.id, 'antispam')
        embed = self.make_status_embed(ctx, 'antispam', actions)
        await ctx.send(embed=embed)

    @antispam.command(name="delete")
    @commands.has_permissions(manage_guild=True)
    async def delete_antispam(self, ctx, on_off: str):
        value = on_off.lower() == 'on'
        self.set_feature_action(ctx.guild.id, 'antispam', 'delete', value)
        actions = self.get_feature_actions(ctx.guild.id, 'antispam')
        embed = self.make_status_embed(ctx, 'antispam', actions)
        await ctx.send(embed=embed)

    @antispam.command(name="warn")
    @commands.has_permissions(manage_guild=True)
    async def warn_antispam(self, ctx, on_off: str):
        value = on_off.lower() == 'on'
        self.set_feature_action(ctx.guild.id, 'antispam', 'warn', value)
        actions = self.get_feature_actions(ctx.guild.id, 'antispam')
        embed = self.make_status_embed(ctx, 'antispam', actions)
        await ctx.send(embed=embed)

    @antispam.command(name="mute")
    @commands.has_permissions(manage_guild=True)
    async def mute_antispam(self, ctx, on_off: str):
        value = on_off.lower() == 'on'
        self.set_feature_action(ctx.guild.id, 'antispam', 'mute', value)
        actions = self.get_feature_actions(ctx.guild.id, 'antispam')
        embed = self.make_status_embed(ctx, 'antispam', actions)
        await ctx.send(embed=embed)

    @commands.group()
    @commands.has_permissions(manage_guild=True)
    async def automodmute(self, ctx):
        """Configure mute duration for automod punishments."""
        await ctx.send("Use subcommands to set mute duration for each feature.")

    @automodmute.command()
    @commands.has_permissions(manage_guild=True)
    async def set(self, ctx, feature: str, duration: str):
        """Set mute duration for a feature. Duration format: 10s, 5m, 2h"""
        units = {'s': 1, 'm': 60, 'h': 3600}
        try:
            if duration[-1] in units:
                seconds = int(duration[:-1]) * units[duration[-1]]
            else:
                seconds = int(duration)
        except Exception:
            await ctx.send("Invalid duration format. Use e.g. 10s, 5m, 2h.")
            return
        config = self.get_guild_config(ctx.guild.id)
        if feature not in config:
            await ctx.send(f"Feature '{feature}' not found or not configured.")
            return
        config[feature]['mute_duration'] = seconds
        await ctx.send(f"Mute duration for **{feature.replace('_',' ').title()}** set to **{duration}**.")

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
    await bot.add_cog(Automod())
