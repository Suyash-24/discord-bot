import discord
import typing
from discord.ext import commands
import json
import os

CUSTOM_ROLE_FILE = "data/customroles.json"

def load_custom_roles():
    if not os.path.exists(CUSTOM_ROLE_FILE):
        with open(CUSTOM_ROLE_FILE, "w") as f:
            json.dump({}, f)
    with open(CUSTOM_ROLE_FILE, "r") as f:
        return json.load(f)

def save_custom_roles(data):
    with open(CUSTOM_ROLE_FILE, "w") as f:
        json.dump(data, f, indent=4)

class CustomRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.custom_roles = load_custom_roles()

    def get_guild_roles(self, guild_id):
        return self.custom_roles.get(str(guild_id), {})

    def set_guild_roles(self, guild_id, data):
        self.custom_roles[str(guild_id)] = data
        save_custom_roles(self.custom_roles)

    @commands.command(name="addcustomrole")
    @commands.has_permissions(administrator=True)
    async def add_custom_role(self, ctx, keyword: str, *, role: discord.Role):
        guild_roles = self.get_guild_roles(ctx.guild.id)
        guild_roles[keyword.lower()] = role.id
        self.set_guild_roles(ctx.guild.id, guild_roles)
        embed = discord.Embed(
            title="✅ Custom Role Mapping Added",
            description=f"`{keyword}` → {role.mention}",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
        await ctx.send(embed=embed)

    @commands.command(name="delcustomrole")
    @commands.has_permissions(administrator=True)
    async def del_custom_role(self, ctx, keyword: str):
        guild_roles = self.get_guild_roles(ctx.guild.id)
        if keyword.lower() in guild_roles:
            del guild_roles[keyword.lower()]
            self.set_guild_roles(ctx.guild.id, guild_roles)
            embed = discord.Embed(
                title="❌ Custom Role Mapping Removed",
                description=f"Removed mapping for `{keyword}`.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url if hasattr(ctx.author, 'display_avatar') else ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="⚠️ No Such Custom Role",
                description="That custom role does not exist.",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def roles(self, ctx):
        roles = self.get_guild_roles(ctx.guild.id)
        if not roles:
            embed = discord.Embed(
                title="❌ No Custom Roles Set",
                description="No custom roles have been set for this server.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            return await ctx.send(embed=embed)
        msg = "\n".join(f"`{k}` → <@&{v}>" for k, v in roles.items())
        embed = discord.Embed(
            title="✨ Custom Role Shortcuts",
            description=msg,
            color=discord.Color.purple(),
            timestamp=discord.utils.utcnow()
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def girl(self, ctx, member: typing.Union[discord.Member, str, int]):
        resolved = await self._resolve_member(ctx, member)
        if not resolved:
            await ctx.send("❌ Could not resolve member.")
            return
        await self.assign_custom(ctx, resolved, "girl")

    @commands.command()
    async def boy(self, ctx, member: typing.Union[discord.Member, str, int]):
        resolved = await self._resolve_member(ctx, member)
        if not resolved:
            await ctx.send("❌ Could not resolve member.")
            return
        await self.assign_custom(ctx, resolved, "boy")

    @commands.command()
    async def any(self, ctx, member: typing.Union[discord.Member, str, int], keyword: str):
        resolved = await self._resolve_member(ctx, member)
        if not resolved:
            await ctx.send("❌ Could not resolve member.")
            return
        await self.assign_custom(ctx, resolved, keyword.lower())

    async def _resolve_member(self, ctx, member):
        if isinstance(member, discord.Member):
            return member
        try:
            member_id = int(member)
            return ctx.guild.get_member(member_id)
        except Exception:
            return None

    async def assign_custom(self, ctx, member, keyword):
        roles = self.get_guild_roles(ctx.guild.id)
        role_id = roles.get(keyword)
        if not role_id:
            embed = discord.Embed(
                title="⚠️ No Role Mapped",
                description=f"No role mapped for `{keyword}`.",
                color=discord.Color.orange(),
                timestamp=discord.utils.utcnow()
            )
            await ctx.send(embed=embed)
            return
        role = ctx.guild.get_role(role_id)
        if not role:
            embed = discord.Embed(
                title="❌ Role Not Found",
                description="The mapped role no longer exists.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            await ctx.send(embed=embed)
            return
        await member.add_roles(role)
        embed = discord.Embed(
            title="✅ Role Added",
            description=f"Added role {role.mention} to {member.mention}.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CustomRoles(bot))
