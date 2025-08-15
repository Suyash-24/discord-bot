import discord
from discord.ext import commands
import json
import os

CONFIG_FILE = "boostconfig.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class BoostEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = load_config()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.premium_since is None and after.premium_since is not None:
            await self.handle_boost(after)
        elif before.premium_since is not None and after.premium_since is None:
            await self.handle_unboost(after)

    async def handle_boost(self, member):
        guild_id = str(member.guild.id)
        guild_config = self.config.get(guild_id, {})

        channel_id = guild_config.get("boost_channel")
        if not channel_id:
            return

        channel = member.guild.get_channel(channel_id)
        if not channel:
            return

        embed_config = guild_config.get("boost_embed", {})
        embed = discord.Embed(
            title=embed_config.get("title", "🚀 New Boost!"),
            description=embed_config.get("description", f"{member.mention} just boosted the server!"),
            color=int(embed_config.get("color", "0xFF73FA"), 16)
        )

        embed.set_footer(text=embed_config.get("footer", "Thank you for boosting!"))
        if "image" in embed_config:
            embed.set_image(url=embed_config["image"])
        if "thumbnail" in embed_config:
            embed.set_thumbnail(url=embed_config["thumbnail"])

        await channel.send(embed=embed)

    async def handle_unboost(self, member):
        guild_id = str(member.guild.id)
        guild_config = self.config.get(guild_id, {})
        channel_id = guild_config.get("boost_channel")

        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                embed = discord.Embed(
                    title="💔 Server Unboosted",
                    description=f"{member.mention} has unboosted the server.",
                    color=discord.Color.red(),
                    timestamp=discord.utils.utcnow()
                )
                embed.set_footer(text="We appreciate your previous support!")
                await channel.send(embed=embed)

    @commands.command(name="setboostchannel")
    @commands.has_permissions(administrator=True)
    async def set_boost_channel(self, ctx, channel: discord.TextChannel):
        guild_id = str(ctx.guild.id)
        self.config.setdefault(guild_id, {})
        self.config[guild_id]["boost_channel"] = channel.id
        save_config(self.config)
        embed = discord.Embed(
            title="✅ Boost Log Channel Set",
            description=f"Boost log channel set to {channel.mention}.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command(name="setboostembed")
    @commands.has_permissions(administrator=True)
    async def set_boost_embed(self, ctx, field: str, *, value: str):
        """Fields: title, description, color (hex), footer, image, thumbnail"""
        guild_id = str(ctx.guild.id)
        self.config.setdefault(guild_id, {})
        self.config[guild_id].setdefault("boost_embed", {})
        self.config[guild_id]["boost_embed"][field.lower()] = value
        save_config(self.config)
        embed = discord.Embed(
            title="✅ Boost Embed Updated",
            description=f"Boost embed `{field}` set to: {value}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(BoostEvents(bot))
