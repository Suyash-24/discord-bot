# This file contains all emoji and sticker management commands for the bot.

import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from io import BytesIO
import aiohttp

class Expressions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def has_manage_expressions():
        async def predicate(ctx):
            perms = ctx.author.guild_permissions
            return perms.manage_emojis_and_stickers or getattr(perms, 'manage_expressions', False)
        return commands.check(predicate)

    # Prefix: Add Emoji
    @commands.command(name="addemoji")
    @has_manage_expressions()
    async def addemoji(self, ctx, name: str, url: Optional[str] = None):
        url = url or (ctx.message.attachments[0].url if ctx.message.attachments else None)
        embed = discord.Embed(title="Add Emoji", color=discord.Color.blurple())
        if not url:
            embed.description = "Please provide an image URL or attach an image."
            return await ctx.send(embed=embed)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    embed.description = "Failed to fetch image."
                    return await ctx.send(embed=embed)
                img = await resp.read()
        try:
            emoji = await ctx.guild.create_custom_emoji(name=name, image=img)
            embed.description = f"✅ Emoji created: <:{emoji.name}:{emoji.id}>"
            embed.color = discord.Color.green()
        except discord.Forbidden:
            embed.description = "I don't have permission to add emojis."
            embed.color = discord.Color.red()
        except Exception as e:
            embed.description = f"Error: {e}"
            embed.color = discord.Color.red()
        await ctx.send(embed=embed)

    # Prefix: Remove Emoji
    @commands.command(name="removeemoji")
    @has_manage_expressions()
    async def removeemoji(self, ctx, emoji: discord.Emoji):
        embed = discord.Embed(title="Remove Emoji", color=discord.Color.blurple())
        try:
            await emoji.delete()
            embed.description = f"✅ Emoji removed: `{emoji.name}`"
            embed.color = discord.Color.green()
        except discord.Forbidden:
            embed.description = "I don't have permission to remove emojis."
            embed.color = discord.Color.red()
        except Exception as e:
            embed.description = f"Error: {e}"
            embed.color = discord.Color.red()
        await ctx.send(embed=embed)

    # Prefix: Steal Emoji/Sticker
    @commands.command(name="steal")
    @has_manage_expressions()
    async def steal(self, ctx, *, arg: Optional[str] = None):
        msg = ctx.message
        target_msg = msg
        if msg.reference:
            try:
                target_msg = await ctx.channel.fetch_message(msg.reference.message_id)
            except Exception:
                pass
        embed = discord.Embed(title="Steal Emoji/Sticker", color=discord.Color.blurple())
        # Steal sticker if present
        if target_msg.stickers:
            sticker = target_msg.stickers[0]
            if sticker.format == discord.StickerFormatType.png:
                url = sticker.url
                name = sticker.name
                await self._add_sticker(ctx, name, url, embed)
                return
            else:
                embed.description = "Only PNG stickers can be stolen."
                return await ctx.send(embed=embed)
        # Steal emoji from message or arg
        if arg:
            custom_emojis = [e for e in arg.split() if e.startswith('<:') or e.startswith('<a:')]
        else:
            custom_emojis = [e for e in target_msg.content.split() if e.startswith('<:') or e.startswith('<a:')]
        if custom_emojis:
            results = []
            for e in custom_emojis:
                try:
                    parts = e.replace('<', '').replace('>', '').split(':')
                    name, eid = parts[1], int(parts[2])
                    emoji_obj = await self.bot.fetch_emoji(eid)
                    url = emoji_obj.url
                    emoji = await self._add_emoji(ctx, name, url, return_emoji=True)
                    if emoji:
                        results.append(f"<:{emoji.name}:{emoji.id}>")
                except Exception as e:
                    results.append(f"❌ Failed: {e}")
            embed.description = "\n".join(results) if results else "No valid emojis found."
            embed.color = discord.Color.green() if results else discord.Color.red()
            return await ctx.send(embed=embed)
        embed.description = "No emoji or sticker found to steal."
        embed.color = discord.Color.red()
        await ctx.send(embed=embed)

    async def _add_emoji(self, ctx, name, url, return_emoji=False):
        async with aiohttp.ClientSession() as session:
            async with session.get(str(url)) as resp:
                if resp.status != 200:
                    if not return_emoji:
                        embed = discord.Embed(title="Steal Emoji", description="Failed to fetch emoji image.", color=discord.Color.red())
                        return await ctx.send(embed=embed)
                    return None
                img = await resp.read()
        try:
            emoji = await ctx.guild.create_custom_emoji(name=name, image=img)
            if not return_emoji:
                embed = discord.Embed(title="Steal Emoji", description=f"✅ Emoji stolen: <:{emoji.name}:{emoji.id}>", color=discord.Color.green())
                await ctx.send(embed=embed)
            return emoji
        except Exception as e:
            if not return_emoji:
                embed = discord.Embed(title="Steal Emoji", description=f"Error: {e}", color=discord.Color.red())
                await ctx.send(embed=embed)
            return None

    async def _add_sticker(self, ctx, name, url, embed=None):
        # Discord API does not allow bots to upload stickers directly
        if embed is None:
            embed = discord.Embed(title="Steal Sticker", color=discord.Color.orange())
        embed.description = "Sticker stealing is limited by Discord API. Please manually upload the sticker."
        await ctx.send(embed=embed)

    # Slash: Add Emoji
    @app_commands.command(name="addemoji", description="Add a custom emoji to the server.")
    async def addemoji_slash(self, interaction: discord.Interaction, name: str, url: str):
        embed = discord.Embed(title="Add Emoji", color=discord.Color.blurple())
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        guild = interaction.guild
        if not guild or not member or not (member.guild_permissions.manage_emojis_and_stickers or getattr(member.guild_permissions, 'manage_expressions', False)):
            embed.description = "You need Manage Emojis and Stickers permission."
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    embed.description = "Failed to fetch image."
                    return await interaction.response.send_message(embed=embed, ephemeral=True)
                img = await resp.read()
        try:
            emoji = await guild.create_custom_emoji(name=name, image=img)
            embed.description = f"✅ Emoji created: <:{emoji.name}:{emoji.id}>"
            embed.color = discord.Color.green()
        except discord.Forbidden:
            embed.description = "I don't have permission to add emojis."
            embed.color = discord.Color.red()
        except Exception as e:
            embed.description = f"Error: {e}"
            embed.color = discord.Color.red()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Slash: Remove Emoji
    @app_commands.command(name="removeemoji", description="Remove a custom emoji from the server.")
    async def removeemoji_slash(self, interaction: discord.Interaction, emoji: str):
        embed = discord.Embed(title="Remove Emoji", color=discord.Color.blurple())
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        guild = interaction.guild
        if not guild or not member or not (member.guild_permissions.manage_emojis_and_stickers or getattr(member.guild_permissions, 'manage_expressions', False)):
            embed.description = "You need Manage Emojis and Stickers permission."
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        # Try to resolve emoji by name or ID
        target_emoji = None
        # Try by ID
        if emoji.isdigit():
            target_emoji = guild.get_emoji(int(emoji))
        # Try by name
        if not target_emoji:
            target_emoji = discord.utils.get(guild.emojis, name=emoji)
        if not target_emoji:
            embed.description = f"Emoji not found: `{emoji}`. Please provide the emoji name or ID."
            embed.color = discord.Color.red()
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        try:
            await target_emoji.delete()
            embed.description = f"✅ Emoji removed: `{target_emoji.name}`"
            embed.color = discord.Color.green()
        except discord.Forbidden:
            embed.description = "I don't have permission to remove emojis."
            embed.color = discord.Color.red()
        except Exception as e:
            embed.description = f"Error: {e}"
            embed.color = discord.Color.red()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Slash: Steal Emoji/Sticker
    @app_commands.command(name="steal", description="Steal one or more emojis or a sticker from another server or message.")
    async def steal_slash(self, interaction: discord.Interaction, emojis: Optional[str] = None):
        embed = discord.Embed(title="Steal Emoji/Sticker", color=discord.Color.blurple())
        member = interaction.user if isinstance(interaction.user, discord.Member) else None
        guild = interaction.guild
        if not guild or not member or not (member.guild_permissions.manage_emojis_and_stickers or getattr(member.guild_permissions, 'manage_expressions', False)):
            embed.description = "You need Manage Emojis and Stickers permission."
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        # Only supports custom emoji string(s) for now
        results = []
        if emojis:
            custom_emojis = [e for e in emojis.split() if e.startswith('<:') or e.startswith('<a:')]
            for e in custom_emojis:
                try:
                    parts = e.replace('<', '').replace('>', '').split(':')
                    name, eid = parts[1], int(parts[2])
                    emoji_obj = await self.bot.fetch_emoji(eid)
                    url = emoji_obj.url
                    emoji = await self._add_emoji_slash(interaction, name, url, return_emoji=True)
                    if emoji:
                        results.append(f"<:{emoji.name}:{emoji.id}>")
                except Exception as e:
                    results.append(f"❌ Failed: {e}")
            embed.description = "\n".join(results) if results else "No valid emojis found."
            embed.color = discord.Color.green() if results else discord.Color.red()
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        embed.description = "No emoji or sticker found to steal."
        embed.color = discord.Color.red()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    async def _add_emoji_slash(self, interaction, name, url, return_emoji=False):
        guild = interaction.guild
        if not guild:
            if not return_emoji:
                embed = discord.Embed(title="Steal Emoji", description="This command can only be used in a server.", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return None
        async with aiohttp.ClientSession() as session:
            async with session.get(str(url)) as resp:
                if resp.status != 200:
                    if not return_emoji:
                        embed = discord.Embed(title="Steal Emoji", description="Failed to fetch emoji image.", color=discord.Color.red())
                        return await interaction.response.send_message(embed=embed, ephemeral=True)
                    return None
                img = await resp.read()
        try:
            emoji = await guild.create_custom_emoji(name=name, image=img)
            if not return_emoji:
                embed = discord.Embed(title="Steal Emoji", description=f"✅ Emoji stolen: <:{emoji.name}:{emoji.id}>", color=discord.Color.green())
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return emoji
        except Exception as e:
            if not return_emoji:
                embed = discord.Embed(title="Steal Emoji", description=f"Error: {e}", color=discord.Color.red())
                await interaction.response.send_message(embed=embed, ephemeral=True)
            return None

async def setup(bot):
    await bot.add_cog(Expressions(bot))
