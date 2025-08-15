
from discord.ext import commands
import discord
from discord import ui
from typing import Optional



class HelpView(ui.View):
    def __init__(self, bot, ctx, modules, home_embed, timeout=120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.ctx = ctx
        self.modules = modules
        self.home_embed = home_embed
        self.add_item(HelpModuleDropdown(modules, bot, ctx, self))

class HelpModuleDropdown(ui.Select):
    def __init__(self, modules, bot, ctx, parent_view):
        options = [discord.SelectOption(label=module, description=f"Show commands in {module}") for module in modules]
        super().__init__(placeholder="Select a module...", min_values=1, max_values=1, options=options)
        self.bot = bot
        self.ctx = ctx
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        module = self.values[0]
        cog = self.bot.get_cog(module)
        if not cog:
            await interaction.response.send_message("Module not found.", ephemeral=True)
            return
        # Use recursive command listing for CustomRoles and Stats
        def get_all_commands_recursive(commands):
            all_cmds = []
            for cmd in commands:
                all_cmds.append(cmd)
                if hasattr(cmd, 'all_commands') and cmd.all_commands:
                    all_cmds.extend(get_all_commands_recursive(cmd.all_commands.values()))
            return all_cmds

        if module in ["CustomRoles", "Stats"]:
            commands_list = get_all_commands_recursive(cog.get_commands())
        else:
            commands_list = cog.get_commands()
        embed = discord.Embed(
            title=f"📦 {module} Commands",
            description=f"Commands in the `{module}` module:",
            color=discord.Color.blurple()
        )
        seen = set()
        for command in commands_list:
            if command.hidden or command.qualified_name in seen:
                continue
            seen.add(command.qualified_name)
            desc = command.help or "No description."
            usage = f"`{self.ctx.prefix}{command.qualified_name} {command.signature}`" if command.signature else f"`{self.ctx.prefix}{command.qualified_name}`"
            embed.add_field(name=usage, value=desc, inline=False)
            if command.checks:
                embed.add_field(name="Checks", value="Has permission checks", inline=False)
        view = ModuleView(self.bot, self.ctx, self.parent_view.modules, self.parent_view.home_embed)
        await interaction.response.edit_message(embed=embed, view=view)

class ModuleView(ui.View):
    def __init__(self, bot, ctx, modules, home_embed, timeout=120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.ctx = ctx
        self.modules = modules
        self.home_embed = home_embed
        self.add_item(HomeButton(home_embed, modules, bot, ctx))

class HomeButton(ui.Button):
    def __init__(self, home_embed, modules, bot, ctx):
        super().__init__(label="🏠 Home", style=discord.ButtonStyle.secondary)
        self.home_embed = home_embed
        self.modules = modules
        self.bot = bot
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        view = HelpView(self.bot, self.ctx, self.modules, self.home_embed)
        await interaction.response.edit_message(embed=self.home_embed, view=view)

def build_module_embed(ctx, bot, module, cog):
    prefix = ctx.prefix
    embed = discord.Embed(
        title=f"📦 {module} Commands",
        description=f"Commands in the `{module}` module:",
        color=discord.Color.blurple()
    )
    for command in cog.get_commands():
        if command.hidden:
            continue
        desc = command.help or "No description."
        # Show correct usage for renamed slash command
        usage_name = command.qualified_name
        if usage_name == "slash_unmute":
            usage_name = "unmuteuser (slash command)"
        usage = f"`{prefix}{usage_name} {command.signature}`" if command.signature else f"`{prefix}{usage_name}`"
        extra = []
        if command.cooldown:
            extra.append(f"⏱️ Cooldown: {command.cooldown.rate}/{command.cooldown.per}s")
        if command.checks:
            extra.append("🔒 Has permission checks")
        if command.aliases:
            extra.append(f"🔀 Aliases: {', '.join(command.aliases)}")
        value = desc
        if extra:
            value += "\n" + "\n".join(extra)
        embed.add_field(name=usage, value=value, inline=False)
    embed.set_footer(text="Use !help <command> for details on a command.")
    return embed

class HelpModuleButton(ui.Button):
    def __init__(self, module, bot, ctx):
        super().__init__(label=module, style=discord.ButtonStyle.primary)
        self.module = module
        self.bot = bot
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        cog = self.bot.get_cog(self.module)
        if not cog:
            await interaction.response.send_message("Module not found.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"📦 {self.module} Commands",
            description=f"Commands in the `{self.module}` module:",
            color=discord.Color.blurple()
        )
        for command in cog.get_commands():
            if command.hidden:
                continue
            desc = command.help or "No description."
            usage = f"`{self.ctx.prefix}{command.qualified_name} {command.signature}`" if command.signature else f"`{self.ctx.prefix}{command.qualified_name}`"
            embed.add_field(name=usage, value=desc, inline=False)
        await interaction.response.edit_message(embed=embed, view=None)

class HelpCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def custom_help(self, ctx, *, arg: Optional[str] = None):
        """
        Shows help for modules, commands, or a specific command.
        Usage:
        - !help : Show all modules
        - !help <module> : Show all commands in a module
        - !help <command> : Show help for a specific command
        """
        prefix = ctx.prefix
        modules = [cog for cog in self.bot.cogs.keys() if self.bot.get_cog(cog)]
        # Ensure CustomRoles and Stats are always present, even if they have no commands
        for forced in ["CustomRoles", "Stats"]:
            if forced not in modules and self.bot.get_cog(forced):
                modules.append(forced)

        # Patch: For CustomRoles and Stats, ensure all commands and subcommands are included in help
        def get_all_commands_recursive(commands):
            all_cmds = []
            for cmd in commands:
                all_cmds.append(cmd)
                if hasattr(cmd, 'all_commands') and cmd.all_commands:
                    all_cmds.extend(get_all_commands_recursive(cmd.all_commands.values()))
            return all_cmds
        # Home embed
        home_embed = discord.Embed(
            title="🤖 Bot Modules",
            description="Select a module from the dropdown below to see its commands, or use `!help <module>` or `!help <command>`.",
            color=discord.Color.blue()
        )
        for module in modules:
            home_embed.add_field(name=f"📦 {module}", value=f"Use `{prefix}help {module}` or select below.", inline=False)
        home_embed.set_footer(text="Use !help <command> for details on a command.")

        if not arg:
            view = HelpView(self.bot, ctx, modules, home_embed)
            await ctx.send(embed=home_embed, view=view)
            return

        # Try to find a module
        cog = self.bot.get_cog(arg)
        if cog:
            embed = discord.Embed(
                title=f"📦 {arg} Commands",
                description=f"Commands in the `{arg}` module:",
                color=discord.Color.blurple()
            )
            # Use recursive get_all_commands for CustomRoles and Stats
            commands_list = get_all_commands_recursive(cog.get_commands()) if arg in ["CustomRoles", "Stats"] else cog.get_commands()
            seen = set()
            for command in commands_list:
                if command.hidden or command.qualified_name in seen:
                    continue
                seen.add(command.qualified_name)
                desc = command.help or "No description."
                usage = f"`{ctx.prefix}{command.qualified_name} {command.signature}`" if command.signature else f"`{ctx.prefix}{command.qualified_name}`"
                embed.add_field(name=usage, value=desc, inline=False)
                if command.checks:
                    embed.add_field(name="Checks", value="Has permission checks", inline=False)
            view = ModuleView(self.bot, ctx, modules, home_embed)
            await ctx.send(embed=embed, view=view)
            return

        # Try to find a command
        command = self.bot.get_command(arg)
        if command:
            embed = discord.Embed(
                title=f"📝 Command: {command.qualified_name}",
                color=discord.Color.green()
            )
            usage = f"`{prefix}{command.qualified_name} {command.signature}`" if command.signature else f"`{prefix}{command.qualified_name}`"
            embed.add_field(name="Usage", value=usage, inline=False)
            embed.add_field(name="Description", value=command.help or "No description.", inline=False)
            if command.aliases:
                embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)
            # Show cooldown and permissions if available
            if command.cooldown:
                embed.add_field(name="Cooldown", value=f"{command.cooldown.rate}/{command.cooldown.per}s", inline=False)
            if command.checks:
                embed.add_field(name="Checks", value="Has permission checks", inline=False)
            await ctx.send(embed=embed)
            return

        # Not found
        await ctx.send(embed=discord.Embed(
            title="❌ Not Found",
            description=f"No module or command named `{arg}` found.",
            color=discord.Color.red()
        ))

async def setup(bot):
    bot.remove_command("help")
    await bot.add_cog(HelpCommand(bot))
