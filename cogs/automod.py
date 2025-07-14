import discord
from discord.ext import commands
from discord import ui

class Automod(commands.Cog):
    """Automod panel and toggles."""

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
