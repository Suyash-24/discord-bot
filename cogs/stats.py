import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta

import json, os
import typing
from collections import defaultdict

STATS_FILE = "data/stats.json"

def load_stats():
    if not os.path.exists(STATS_FILE):
        with open(STATS_FILE, "w") as f:
            json.dump({}, f)
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_period_key(period):
    now = datetime.utcnow()
    if period == "daily":
        return now.strftime("%Y-%m-%d")
    elif period == "weekly":
        return now.strftime("%Y-W%U")
    elif period == "monthly":
        return now.strftime("%Y-%m")
    else:
        return "all"

class Stats(commands.Cog):

    def load_ignored_channels(self):
        ignore_file = "data/ignored_channels.json"
        if os.path.exists(ignore_file):
            with open(ignore_file, "r") as f:
                self.ignored_channels = set(json.load(f))
        else:
            self.ignored_channels = set()

    def save_ignored_channels(self):
        ignore_file = "data/ignored_channels.json"
        with open(ignore_file, "w") as f:
            json.dump(list(self.ignored_channels), f, indent=2)

    # --- Ignore Channel Commands ---


    @commands.command(name="ignore_channel")
    @commands.has_permissions(administrator=True)
    async def ignore_channel(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        channel = channel or ctx.channel
        self.ignored_channels.add(str(channel.id))
        self.save_ignored_channels()
        await ctx.send(f"✅ Channel {channel.mention} is now ignored in stats.")

    @commands.command(name="unignore_channel")
    @commands.has_permissions(administrator=True)
    async def unignore_channel(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        channel = channel or ctx.channel
        self.ignored_channels.discard(str(channel.id))
        self.save_ignored_channels()
        await ctx.send(f"✅ Channel {channel.mention} is no longer ignored in stats.")

    # --- Leaderboard Commands ---
    @commands.group(name="leaderboard", invoke_without_command=True)
    async def leaderboard(self, ctx):
        await ctx.send("Use a subcommand: messages or vc, and period: daily, weekly, monthly, all")

    @leaderboard.command(name="messages")
    async def leaderboard_messages(self, ctx, period: str = "all"):
        guild_id = str(ctx.guild.id)
        gstats = self.stats_data.get(guild_id, {})
        leaderboard = []
        key = get_period_key(period)
        for user_id, udata in gstats.items():
            if user_id == "channels":
                continue
            value = udata.get("messages", {}).get(period, {}).get(key, 0)
            leaderboard.append((user_id, value))
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        embed = discord.Embed(title=f"🏆 Top Messages ({period})", color=discord.Color.gold())
        for user_id, value in leaderboard[:10]:
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else user_id
            embed.add_field(name=name, value=value)
        await ctx.send(embed=embed)

    @leaderboard.command(name="vc")
    async def leaderboard_vc(self, ctx, period: str = "all"):
        guild_id = str(ctx.guild.id)
        gstats = self.stats_data.get(guild_id, {})
        leaderboard = []
        key = get_period_key(period)
        for user_id, udata in gstats.items():
            if user_id == "channels":
                continue
            value = udata.get("vc_time", {}).get(period, {}).get(key, 0)
            leaderboard.append((user_id, value))
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        embed = discord.Embed(title=f"🏆 Top VC Time ({period})", color=discord.Color.purple())
        for user_id, value in leaderboard[:10]:
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else user_id
            embed.add_field(name=name, value=f"{int(value//60)} min")
        await ctx.send(embed=embed)

    def __init__(self, bot):
        self.bot = bot
        self.stats_data = load_stats()
        self.voice_sessions = {}  # user_id: (channel_id, join_time)
        self.ignored_channels = set()
        self.load_ignored_channels()
        self.save_task.start()

    def cog_unload(self):
        self.save_task.cancel()
        save_stats(self.stats_data)

    @tasks.loop(minutes=5)
    async def save_task(self):
        save_stats(self.stats_data)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            if str(message.channel.id) in self.ignored_channels:
                return
        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
        guild_id = str(message.guild.id)
        if channel_id in self.ignored_channels:
            return
        now = datetime.utcnow()
        for period in ["daily", "weekly", "monthly", "all"]:
            key = get_period_key(period)
            self.stats_data.setdefault(guild_id, {}).setdefault(user_id, {}).setdefault("messages", {}).setdefault(period, {}).setdefault(key, 0)
            self.stats_data[guild_id][user_id]["messages"][period][key] += 1
            self.stats_data[guild_id][user_id].setdefault("channels", {}).setdefault(channel_id, {}).setdefault(period, {}).setdefault(key, 0)
            self.stats_data[guild_id][user_id]["channels"][channel_id][period][key] += 1
            # Per-channel stats
            self.stats_data.setdefault(guild_id, {}).setdefault("channels", {}).setdefault(channel_id, {}).setdefault("messages", {}).setdefault(period, {}).setdefault(key, 0)
            self.stats_data[guild_id]["channels"][channel_id]["messages"][period][key] += 1

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or not member.guild:
            return
        # Ignore VC stats if channel is ignored
        if before.channel and str(before.channel.id) in self.ignored_channels:
            return
        if after.channel and str(after.channel.id) in self.ignored_channels:
            return
        user_id = str(member.id)
        guild_id = str(member.guild.id)
        now = datetime.utcnow()
        # User joins a VC
        if after.channel and not before.channel:
            self.voice_sessions[user_id] = (after.channel.id, now)
        # User leaves a VC
        elif before.channel and not after.channel:
            if user_id in self.voice_sessions:
                join_channel, join_time = self.voice_sessions.pop(user_id)
                duration = (now - join_time).total_seconds()
                for period in ["daily", "weekly", "monthly", "all"]:
                    key = get_period_key(period)
                    self.stats_data.setdefault(guild_id, {}).setdefault(user_id, {}).setdefault("vc_time", {}).setdefault(period, {}).setdefault(key, 0)
                    self.stats_data[guild_id][user_id]["vc_time"][period][key] += duration
                    self.stats_data[guild_id][user_id].setdefault("vc_channels", {}).setdefault(str(join_channel), {}).setdefault(period, {}).setdefault(key, 0)
                    self.stats_data[guild_id][user_id]["vc_channels"][str(join_channel)][period][key] += duration
                    # Per-channel stats
                    self.stats_data.setdefault(guild_id, {}).setdefault("channels", {}).setdefault(str(join_channel), {}).setdefault("vc_time", {}).setdefault(period, {}).setdefault(key, 0)
                    self.stats_data[guild_id]["channels"][str(join_channel)]["vc_time"][period][key] += duration

    # --- Commands ---
    @commands.group(invoke_without_command=True)
    async def stats(self, ctx):
        embed = discord.Embed(title="📊 Server Statistics", description="Use subcommands for more details.", color=discord.Color.blurple())
        embed.add_field(name="channel", value="See a channel's stats.", inline=False)
        embed.add_field(name="chart", value="Generate a detailed chart.", inline=False)
        embed.add_field(name="me", value="See your stats in this server.", inline=False)
        embed.add_field(name="server", value="See an overview of the server's stats.", inline=False)
        embed.add_field(name="stats", value="See an overview of a type of stats.", inline=False)
        embed.add_field(name="top", value="See a list of top members and channels.", inline=False)
        embed.add_field(name="user", value="See a user's stats in this server.", inline=False)
        await ctx.send(embed=embed)

    @stats.command()
    async def me(self, ctx):
        user_id = str(ctx.author.id)
        guild_id = str(ctx.guild.id)
        user_stats = self.stats_data.get(guild_id, {}).get(user_id, {})
        embed = discord.Embed(title=f"📈 Stats for {ctx.author.display_name}", color=discord.Color.green())
        for period in ["daily", "weekly", "monthly", "all"]:
            key = get_period_key(period)
            msg_count = user_stats.get("messages", {}).get(period, {}).get(key, 0)
            vc_time = user_stats.get("vc_time", {}).get(period, {}).get(key, 0)
            embed.add_field(name=f"Messages ({period})", value=msg_count, inline=True)
            embed.add_field(name=f"VC Time ({period})", value=f"{int(vc_time//60)} min", inline=True)
        await ctx.send(embed=embed)

    @stats.command()
    async def user(self, ctx, member: typing.Union[discord.Member, str, int]):
        resolved = None
        if isinstance(member, discord.Member):
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
        user_id = str(resolved.id)
        guild_id = str(ctx.guild.id)
        user_stats = self.stats_data.get(guild_id, {}).get(user_id, {})
        display_name = resolved.display_name if hasattr(resolved, 'display_name') else str(resolved)
        embed = discord.Embed(title=f"📈 Stats for {display_name}", color=discord.Color.green())
        for period in ["daily", "weekly", "monthly", "all"]:
            key = get_period_key(period)
            msg_count = user_stats.get("messages", {}).get(period, {}).get(key, 0)
            vc_time = user_stats.get("vc_time", {}).get(period, {}).get(key, 0)
            embed.add_field(name=f"Messages ({period})", value=msg_count, inline=True)
            embed.add_field(name=f"VC Time ({period})", value=f"{int(vc_time//60)} min", inline=True)
        await ctx.send(embed=embed)

    @stats.command()
    async def channel(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        channel = channel or ctx.channel
        channel_id = str(channel.id)
        guild_id = str(ctx.guild.id)
        ch_stats = self.stats_data.get(guild_id, {}).get("channels", {}).get(channel_id, {})
        embed = discord.Embed(title=f"#️⃣ Stats for {channel.name}", color=discord.Color.blurple())
        for period in ["daily", "weekly", "monthly", "all"]:
            key = get_period_key(period)
            msg_count = ch_stats.get("messages", {}).get(period, {}).get(key, 0)
            vc_time = ch_stats.get("vc_time", {}).get(period, {}).get(key, 0)
            embed.add_field(name=f"Messages ({period})", value=msg_count, inline=True)
            embed.add_field(name=f"VC Time ({period})", value=f"{int(vc_time//60)} min", inline=True)
        await ctx.send(embed=embed)

    @stats.command()
    async def server(self, ctx):
        guild_id = str(ctx.guild.id)
        gstats = self.stats_data.get(guild_id, {})
        total_msgs = 0
        total_vc = 0
        for user_id, udata in gstats.items():
            if user_id == "channels":
                continue
            for period in ["daily", "weekly", "monthly", "all"]:
                key = get_period_key(period)
                total_msgs += udata.get("messages", {}).get(period, {}).get(key, 0)
                total_vc += udata.get("vc_time", {}).get(period, {}).get(key, 0)
        embed = discord.Embed(title="🌐 Server Stats", color=discord.Color.blurple())
        embed.add_field(name="Total Messages (all)", value=total_msgs)
        embed.add_field(name="Total VC Time (all)", value=f"{int(total_vc//60)} min")
        await ctx.send(embed=embed)

    @stats.command()
    async def top(self, ctx, stat_type: str = "messages", period: str = "all"):
        guild_id = str(ctx.guild.id)
        gstats = self.stats_data.get(guild_id, {})
        leaderboard = []
        key = get_period_key(period)
        for user_id, udata in gstats.items():
            if user_id == "channels":
                continue
            value = udata.get(stat_type, {}).get(period, {}).get(key, 0)
            leaderboard.append((user_id, value))
        leaderboard.sort(key=lambda x: x[1], reverse=True)
        embed = discord.Embed(title=f"🏆 Top {stat_type.title()} ({period})", color=discord.Color.gold())
        for user_id, value in leaderboard[:10]:
            member = ctx.guild.get_member(int(user_id))
            name = member.display_name if member else user_id
            embed.add_field(name=name, value=value)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))
    # Register with help command if custom help is used
    if hasattr(bot, "help_command") and hasattr(bot.help_command, "add_cog"):
        bot.help_command.add_cog("Stats", "Server and user statistics, leaderboards, and more.")
