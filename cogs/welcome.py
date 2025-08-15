import discord
from discord.ext import commands
from discord import app_commands
import json
import os

WELCOME_CONFIG_FILE = "data/welcome_config.json"

# Helper functions for config

def load_welcome_config():
    if not os.path.exists(WELCOME_CONFIG_FILE):
        with open(WELCOME_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(WELCOME_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_welcome_config(data):
    with open(WELCOME_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def format_placeholders(text, member):
    if not text or not member:
        return text
    guild = getattr(member, 'guild', None)
    def safe(attr, default=""):
        return getattr(member, attr, default) or default
    def safe_guild(attr, default=""):
        return getattr(guild, attr, default) if guild else default
    avatar_url = getattr(getattr(member, 'display_avatar', None), 'url', "")
    return (
        text.replace("{member_name}", safe('name'))
            .replace("{member_display}", safe('display_name'))
            .replace("{member_mention}", safe('mention'))
            .replace("{member_id}", str(safe('id')))
            .replace("{member_avatar}", avatar_url)
            .replace("{guild_name}", safe_guild('name'))
            .replace("{member_count}", str(safe_guild('member_count')))
    )

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_welcome_config()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.guild:
            return
        guild_id = str(member.guild.id)
        conf = self.config.get(guild_id, {})
        channel_id = conf.get("channel")
        if not channel_id:
            return
        channel = member.guild.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return
        # Build embed with dynamic placeholders
        embed_conf = conf.get("embed", {})
        embed = discord.Embed(
            title=format_placeholders(embed_conf.get("title", f"👋 Welcome to {member.guild.name}!"), member),
            description=format_placeholders(embed_conf.get("description", f"{member.mention}, we're glad to have you here!"), member),
            color=int(embed_conf.get("color", "0x00FFB0"), 16)
        )
        if "image" in embed_conf:
            embed.set_image(url=format_placeholders(embed_conf["image"], member))
        if "thumbnail" in embed_conf:
            embed.set_thumbnail(url=format_placeholders(embed_conf["thumbnail"], member))
        embed.set_footer(text=format_placeholders(embed_conf.get("footer", f"Member #{member.guild.member_count}"), member))
        await channel.send(content=format_placeholders(conf.get("message", ""), member), embed=embed)
        # DM welcome
        if conf.get("dm_enabled", False):
            try:
                dm_embed = discord.Embed(
                    title=format_placeholders(embed_conf.get("dm_title", "👋 Welcome!"), member),
                    description=format_placeholders(embed_conf.get("dm_description", f"Welcome to {member.guild.name}, {member.mention}!"), member),
                    color=int(embed_conf.get("dm_color", "0x00FFB0"), 16)
                )
                await member.send(embed=dm_embed)
            except Exception:
                pass

    # Admin commands for full customization
    @app_commands.command(name="setwelcomechannel", description="Set the welcome channel.")
    @commands.has_permissions(administrator=True)
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        gid = str(interaction.guild.id)
        self.config.setdefault(gid, {})
        self.config[gid]["channel"] = channel.id
        save_welcome_config(self.config)
        embed = discord.Embed(
            title="✅ Welcome Channel Set",
            description=f"Welcome channel set to {channel.mention}.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setwelcomemessage", description="Set the welcome message (text before embed)")
    @commands.has_permissions(administrator=True)
    async def set_welcome_message(self, interaction: discord.Interaction, message: str):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        gid = str(interaction.guild.id)
        self.config.setdefault(gid, {})
        self.config[gid]["message"] = message
        save_welcome_config(self.config)
        embed = discord.Embed(
            title="✅ Welcome Message Set",
            description=f"Welcome message set!",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setwelcomeembed", description="Customize the welcome embed (JSON)")
    @commands.has_permissions(administrator=True)
    async def set_welcome_embed(self, interaction: discord.Interaction, *, embed_json: str):
        """JSON fields: title, description, color (hex), image, thumbnail, footer, dm_title, dm_description, dm_color"""
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        gid = str(interaction.guild.id)
        self.config.setdefault(gid, {})
        try:
            embed_conf = json.loads(embed_json)
            self.config[gid]["embed"] = embed_conf
            save_welcome_config(self.config)
            embed = discord.Embed(
                title="✅ Welcome Embed Updated",
                description="Welcome embed updated!",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Invalid JSON",
                description=f"Error: {e}",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="togglewelcomedm", description="Enable or disable welcome DMs")
    @commands.has_permissions(administrator=True)
    async def toggle_welcome_dm(self, interaction: discord.Interaction, enabled: bool):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        gid = str(interaction.guild.id)
        self.config.setdefault(gid, {})
        self.config[gid]["dm_enabled"] = enabled
        save_welcome_config(self.config)
        embed = discord.Embed(
            title="✅ Welcome DM Toggled",
            description=f"Welcome DMs are now {'enabled' if enabled else 'disabled'}.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="previewwelcome", description="Preview the welcome message as admin")
    @commands.has_permissions(administrator=True)
    async def preview_welcome(self, interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        gid = str(interaction.guild.id)
        conf = self.config.get(gid, {})
        channel_id = conf.get("channel")
        channel = interaction.guild.get_channel(channel_id) if channel_id else None
        embed_conf = conf.get("embed", {})
        # Use the admin as the member for preview placeholders, fallback to a mock if not a Member
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        if not member:
            class Dummy:
                name = "PreviewUser"
                display_name = "PreviewUser"
                mention = "@PreviewUser"
                id = 0
                display_avatar = type("Avatar", (), {"url": "https://cdn.discordapp.com/embed/avatars/0.png"})()
                guild = interaction.guild
            member = Dummy()
        embed = discord.Embed(
            title=format_placeholders(embed_conf.get("title", f"👋 Welcome to {interaction.guild.name}!"), member),
            description=format_placeholders(embed_conf.get("description", f"{interaction.user.mention}, we're glad to have you here!"), member),
            color=int(embed_conf.get("color", "0x00FFB0"), 16)
        )
        if "image" in embed_conf:
            embed.set_image(url=format_placeholders(embed_conf["image"], member))
        if "thumbnail" in embed_conf:
            embed.set_thumbnail(url=format_placeholders(embed_conf["thumbnail"], member))
        embed.set_footer(text=format_placeholders(embed_conf.get("footer", f"Member #{interaction.guild.member_count}"), member))
        await interaction.response.send_message(content=format_placeholders(conf.get("message", ""), member), embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))
