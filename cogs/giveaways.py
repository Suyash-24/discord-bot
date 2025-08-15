import discord
from discord.ext import commands, tasks
from discord import app_commands

import asyncio
import json
import time
import random
from utils import modutils

GIVEAWAYS_FILE = "giveaways.json"

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_giveaways.start()

    def cog_unload(self):
        self.check_giveaways.cancel()

    def load_giveaways(self):
        try:
            with open(GIVEAWAYS_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_giveaways(self, data):
        with open(GIVEAWAYS_FILE, "w") as f:
            json.dump(data, f, indent=4)

    @tasks.loop(seconds=30)
    async def check_giveaways(self):
        data = self.load_giveaways()
        ended = []
        for msg_id, g in data.items():
            if time.time() >= g["end_time"]:
                channel = self.bot.get_channel(g["channel_id"])
                if channel:
                    try:
                        message = await channel.fetch_message(int(msg_id))
                        users = [user async for user in message.reactions[0].users() if not user.bot]
                        if users:
                            winner = random.choice(users)
                            await channel.send(f"🎉 Congratulations {winner.mention}! You won **{g['prize']}**!")
                        else:
                            await channel.send("😢 No one entered the giveaway.")
                    except Exception as e:
                        print(f"Error ending giveaway: {e}")
                ended.append(msg_id)
        for msg_id in ended:
            data.pop(msg_id)
        self.save_giveaways(data)

    @app_commands.command(name="start_giveaway", description="Start a giveaway")
    @app_commands.describe(
        duration="Duration in seconds",
        prize="Prize of the giveaway",
        channel="Channel where to host the giveaway"
    )
    async def start_giveaway(self, interaction: discord.Interaction, duration: int, prize: str, channel: discord.TextChannel):
        if not isinstance(interaction.user, discord.Member) or not modutils.is_mod_user(interaction.user):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to start a giveaway.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        end_time = int(time.time()) + duration
        embed = discord.Embed(
            title="🎉 Giveaway Started!",
            description=f"**Prize:** {prize}\nReact with 🎉 to enter!\n**Ends:** <t:{end_time}:R>",
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Giveaway started by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url if hasattr(interaction.user, 'display_avatar') else interaction.user.avatar.url if interaction.user.avatar else None)

        message = await channel.send(embed=embed)
        await message.add_reaction("🎉")

        data = self.load_giveaways()
        data[str(message.id)] = {
            "prize": prize,
            "channel_id": channel.id,
            "end_time": end_time
        }
        self.save_giveaways(data)

        confirm_embed = discord.Embed(
            title="✅ Giveaway Created",
            description=f"Giveaway started in {channel.mention} for **{prize}**!",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)

    @app_commands.command(name="end_giveaway", description="End a giveaway early")
    async def end_giveaway(self, interaction: discord.Interaction, message_id: str):
        if not isinstance(interaction.user, discord.Member) or not modutils.is_mod_user(interaction.user):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to end giveaways.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        data = self.load_giveaways()
        if message_id not in data:
            embed = discord.Embed(
                title="❌ Not Found",
                description="No giveaway found with that message ID.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        g = data.pop(message_id)
        self.save_giveaways(data)

        channel = self.bot.get_channel(g["channel_id"])
        if channel:
            try:
                message = await channel.fetch_message(int(message_id))
                users = [user async for user in message.reactions[0].users() if not user.bot]
                if users:
                    winner = random.choice(users)
                    win_embed = discord.Embed(
                        title="🎉 Giveaway Ended Early!",
                        description=f"Winner: {winner.mention} for **{g['prize']}**!",
                        color=discord.Color.purple(),
                        timestamp=discord.utils.utcnow()
                    )
                    await channel.send(embed=win_embed)
                else:
                    no_part_embed = discord.Embed(
                        title="😢 Giveaway Ended Early",
                        description="No participants in the giveaway.",
                        color=discord.Color.orange(),
                        timestamp=discord.utils.utcnow()
                    )
                    await channel.send(embed=no_part_embed)
            except Exception as e:
                print(f"Error ending giveaway early: {e}")
        confirm_embed = discord.Embed(
            title="✅ Giveaway Ended",
            description="The giveaway has been ended early.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)

    @app_commands.command(name="cancel_giveaway", description="Cancel a giveaway without winner")
    async def cancel_giveaway(self, interaction: discord.Interaction, message_id: str):
        if not isinstance(interaction.user, discord.Member) or not modutils.is_mod_user(interaction.user):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to cancel giveaways.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        data = self.load_giveaways()
        if message_id not in data:
            embed = discord.Embed(
                title="❌ Not Found",
                description="No giveaway found with that message ID.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        g = data.pop(message_id)
        self.save_giveaways(data)

        channel = self.bot.get_channel(g["channel_id"])
        if channel:
            cancel_embed = discord.Embed(
                title="🚫 Giveaway Cancelled",
                description=f"Giveaway for **{g['prize']}** has been cancelled.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await channel.send(embed=cancel_embed)
        confirm_embed = discord.Embed(
            title="✅ Giveaway Cancelled",
            description="The giveaway has been cancelled.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)

    @app_commands.command(name="reroll_giveaway", description="Reroll a giveaway winner")
    async def reroll_giveaway(self, interaction: discord.Interaction, message_id: str):
        if not isinstance(interaction.user, discord.Member) or not modutils.is_mod_user(interaction.user):
            embed = discord.Embed(
                title="❌ Permission Denied",
                description="You don't have permission to reroll giveaways.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        data = self.load_giveaways()
        g = data.get(message_id)
        if not g:
            embed = discord.Embed(
                title="❌ Not Found",
                description="Giveaway not found.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        channel = self.bot.get_channel(g["channel_id"])
        try:
            message = await channel.fetch_message(int(message_id))
            users = [user async for user in message.reactions[0].users() if not user.bot]
            if users:
                winner = random.choice(users)
                reroll_embed = discord.Embed(
                    title="🔄 Giveaway Rerolled",
                    description=f"Rerolled winner: {winner.mention} for **{g['prize']}**!",
                    color=discord.Color.purple(),
                    timestamp=discord.utils.utcnow()
                )
                await channel.send(embed=reroll_embed)
            else:
                no_part_embed = discord.Embed(
                    title="😢 No Participants",
                    description="No participants to reroll.",
                    color=discord.Color.orange(),
                    timestamp=discord.utils.utcnow()
                )
                await channel.send(embed=no_part_embed)
        except Exception as e:
            print(f"Error rerolling: {e}")
        confirm_embed = discord.Embed(
            title="✅ Giveaway Rerolled",
            description="The giveaway has been rerolled.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=confirm_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Giveaways(bot))
