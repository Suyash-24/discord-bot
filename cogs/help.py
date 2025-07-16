from discord.ext import commands
import discord

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def custom_help(self, ctx):
        embed = discord.Embed(
            title="🤖 Bot Commands",
            description="Here's a list of available commands:",
            color=discord.Color.blue()
        )
        embed.add_field(name="`!ping`", value="Check bot latency", inline=False)
        embed.add_field(name="`!setprefix <prefix>`", value="Set custom server prefix (Admin)", inline=False)
        embed.add_field(name="`!no_prefix add/remove @user`", value="Add or remove no-prefix access", inline=False)
        # Add more commands here as you add them

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommand(bot))
