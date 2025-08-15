import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import datetime
import pytz
import os

BIRTHDAYS_FILE = "data/birthdays.json"
CONFIG_FILE = "data/birthday_config.json"
EMBED_FILE = "data/birthday_embeds.json"

def load_json(path): return json.load(open(path, "r", encoding="utf-8")) if os.path.exists(path) else {}
def save_json(path, data): json.dump(data, open(path, "w", encoding="utf-8"), indent=4)

class Birthday(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.birthdays = load_json(BIRTHDAYS_FILE)
        self.config = load_json(CONFIG_FILE)
        self.embeds = load_json(EMBED_FILE)
        self.check_birthdays.start()

    def cog_unload(self):
        self.check_birthdays.cancel()

    # -- Commands --

    @app_commands.command(name="setbirthday", description="Set your birthday (format: DD-MM)")
    async def set_birthday(self, interaction: discord.Interaction, date: str):
        try:
            day, month = map(int, date.split("-"))
            datetime.datetime(2000, month, day)  # validate
            self.birthdays[str(interaction.user.id)] = {"day": day, "month": month}
            save_json(BIRTHDAYS_FILE, self.birthdays)
            embed = discord.Embed(
                title="🎉 Birthday Set!",
                description=f"Your birthday is set to `{day:02d}-{month:02d}`.",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url if hasattr(interaction.user, 'display_avatar') else interaction.user.avatar.url if interaction.user.avatar else None)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            embed = discord.Embed(
                title="❌ Invalid Format",
                description="Please use the format `DD-MM`.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="viewbirthday", description="View your birthday")
    async def view_birthday(self, interaction: discord.Interaction):
        data = self.birthdays.get(str(interaction.user.id))
        if data:
            embed = discord.Embed(
                title="🎂 Your Birthday",
                description=f"Your birthday is set to `{data['day']:02d}-{data['month']:02d}`.",
                color=discord.Color.pink(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="❌ Not Set",
                description="You haven't set your birthday yet.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="resetbirthday", description="Reset your birthday")
    async def reset_birthday(self, interaction: discord.Interaction):
        if str(interaction.user.id) in self.birthdays:
            del self.birthdays[str(interaction.user.id)]
            save_json(BIRTHDAYS_FILE, self.birthdays)
            embed = discord.Embed(
                title="🔄 Birthday Reset",
                description="Your birthday has been reset.",
                color=discord.Color.yellow(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="❌ Not Set",
                description="You don't have a birthday set.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="viewallbirthdays", description="Admin only: View all upcoming birthdays")
    @commands.has_permissions(administrator=True)
    async def view_all(self, interaction: discord.Interaction):
        guild = interaction.guild
        upcoming = []
        today = datetime.datetime.utcnow().date()
        if not guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        for uid, data in self.birthdays.items():
            user = guild.get_member(int(uid)) if guild else None
            if user:
                bday = datetime.date(today.year, data["month"], data["day"])
                days_left = (bday - today).days
                if days_left < 0:
                    bday = datetime.date(today.year + 1, data["month"], data["day"])
                    days_left = (bday - today).days
                upcoming.append((user.name, data["day"], data["month"], days_left))
        upcoming.sort(key=lambda x: x[3])
        lines = [f"🎂 **{u}** – {d:02d}/{m:02d} ({days} days)" for u, d, m, days in upcoming[:10]]
        embed = discord.Embed(
            title="🎉 Upcoming Birthdays",
            description="\n".join(lines) or "No birthdays set.",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setbdaychannel", description="Set birthday announcement channel")
    @commands.has_permissions(administrator=True)
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not interaction.guild:
            embed = discord.Embed(
                title="❌ Server Only",
                description="This command can only be used in a server.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.config[str(interaction.guild.id)] = self.config.get(str(interaction.guild.id), {})
        self.config[str(interaction.guild.id)]["channel"] = channel.id
        save_json(CONFIG_FILE, self.config)
        embed = discord.Embed(
            title="✅ Birthday Channel Set",
            description=f"Birthday channel set to {channel.mention}.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="settimezone", description="Set server timezone (e.g., Asia/Kolkata)")
    @commands.has_permissions(administrator=True)
    async def set_timezone(self, interaction: discord.Interaction, timezone: str):
        if not interaction.guild:
            embed = discord.Embed(
                title="❌ Server Only",
                description="This command can only be used in a server.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        if timezone not in pytz.all_timezones:
            embed = discord.Embed(
                title="❌ Invalid Timezone",
                description="Please provide a valid timezone.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.config[str(interaction.guild.id)] = self.config.get(str(interaction.guild.id), {})
        self.config[str(interaction.guild.id)]["timezone"] = timezone
        save_json(CONFIG_FILE, self.config)
        embed = discord.Embed(
            title="🕒 Timezone Set",
            description=f"Timezone set to `{timezone}`.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="setbirthdayembed", description="Customize the birthday embed")
    @commands.has_permissions(administrator=True)
    async def set_embed(self, interaction: discord.Interaction, title: str, message: str, color: str = "#FFC0CB"):
        if not interaction.guild:
            embed = discord.Embed(
                title="❌ Server Only",
                description="This command can only be used in a server.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        self.embeds[str(interaction.guild.id)] = {
            "title": title, "description": message, "color": color
        }
        save_json(EMBED_FILE, self.embeds)
        embed = discord.Embed(
            title="✅ Birthday Embed Updated",
            description="Birthday embed updated!",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -- Background Task --

    @tasks.loop(hours=24)
    async def check_birthdays(self):
        now = datetime.datetime.utcnow()
        for guild in self.bot.guilds:
            if not guild:
                continue
            gid = str(guild.id)
            conf = self.config.get(gid, {})
            timezone = pytz.timezone(conf.get("timezone", "UTC"))
            today = datetime.datetime.now(timezone)
            channel_id = conf.get("channel")
            if not channel_id:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            for uid, data in self.birthdays.items():
                if data["day"] == today.day and data["month"] == today.month:
                    user = guild.get_member(int(uid)) if guild else None
                    if user:
                        embed_conf = self.embeds.get(gid, {})
                        embed = discord.Embed(
                            title=embed_conf.get("title", "🎂 Happy Birthday!"),
                            description=embed_conf.get("description", f"Wishing {user.mention} a fantastic day! 🎉"),
                            color=int(embed_conf.get("color", "#FFC0CB").strip("#"), 16)
                        )
                        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
                        await channel.send(content=f"🎉 Happy Birthday {user.mention}!", embed=embed)
                        try:
                            await user.send(f"🎈 Happy Birthday, {user.name}! Have an amazing day!")
                        except:
                            pass

    @check_birthdays.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Birthday(bot))
