import discord
from discord.ext import commands
import json
from typing import Optional
from utils.modutils import log_mod_action

MODLOGS_FILE = "data/modlogs.json"

class Events(commands.Cog):
    # Voice state updates (join/leave/move/mute/deafen)
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel:
            if before.channel and not after.channel:
                await log_mod_action(member.guild, "voice_leave", member, member, f"Left voice channel: {before.channel.name}")
            elif not before.channel and after.channel:
                await log_mod_action(member.guild, "voice_join", member, member, f"Joined voice channel: {after.channel.name}")
            elif before.channel and after.channel and before.channel != after.channel:
                await log_mod_action(member.guild, "voice_move", member, member, f"Moved: {before.channel.name} → {after.channel.name}")
        if before.self_mute != after.self_mute:
            state = "Muted" if after.self_mute else "Unmuted"
            await log_mod_action(member.guild, "voice_self_mute", member, member, f"{state} themselves in voice.")
        if before.self_deaf != after.self_deaf:
            state = "Deafened" if after.self_deaf else "Undeafened"
            await log_mod_action(member.guild, "voice_self_deaf", member, member, f"{state} themselves in voice.")


    # Thread events
    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        await log_mod_action(thread.guild, "thread_create", thread.owner or thread.guild.me, thread.guild.me, f"Thread created: {thread.name}")

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        await log_mod_action(thread.guild, "thread_delete", thread.owner or thread.guild.me, thread.guild.me, f"Thread deleted: {thread.name}")

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        await log_mod_action(after.guild, "thread_update", after.owner or after.guild.me, after.guild.me, f"Thread updated: {before.name} → {after.name}")

    # Integration events
    @commands.Cog.listener()
    async def on_guild_integrations_update(self, guild):
        await log_mod_action(guild, "integrations_update", guild.me, guild.me, "Guild integrations updated.")

    # Webhook events
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel):
        await log_mod_action(channel.guild, "webhook_update", channel.guild.me, channel.guild.me, f"Webhooks updated in {channel.mention}")

    # Scheduled event events
    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event):
        await log_mod_action(event.guild, "scheduled_event_create", event.creator or event.guild.me, event.guild.me, f"Scheduled event created: {event.name}")

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event):
        await log_mod_action(event.guild, "scheduled_event_delete", event.creator or event.guild.me, event.guild.me, f"Scheduled event deleted: {event.name}")

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before, after):
        await log_mod_action(after.guild, "scheduled_event_update", after.creator or after.guild.me, after.guild.me, f"Scheduled event updated: {before.name} → {after.name}")

    # Audit log entry create (if privileged intent enabled)
    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry, guild):
        await log_mod_action(guild, "audit_log_entry", entry.user or guild.me, guild.me, f"Audit log action: {entry.action}")
    @commands.command(name="logevents", help="List all loggable event types.")
    async def logevents(self, ctx):
        events = [
            "member_join", "member_leave", "message_delete", "message_edit", "channel_create", "channel_delete", "channel_update",
            "role_create", "role_delete", "role_update", "ban", "unban", "nickname", "roleadd", "roleremove", "guild_update",
            "emoji_add", "emoji_remove", "sticker_add", "sticker_remove", "invite_create", "invite_delete", "mute", "unmute", "warn"
        ]
        await ctx.send(embed=discord.Embed(title="Loggable Events", description="\n".join(events), color=discord.Color.blurple()))

    @commands.command(name="logembedset", help="Set embed color/title/icon for a specific event type.")
    @commands.has_permissions(administrator=True)
    async def logembedset(self, ctx, event: str, color: Optional[str] = None, *, title: Optional[str] = None):
        try:
            with open(MODLOGS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        conf = data.setdefault(str(ctx.guild.id), {})
        event_embeds = conf.setdefault("event_embeds", {})
        event_conf = event_embeds.setdefault(event, {})
        if color:
            try:
                event_conf["color"] = int(color.strip("#"), 16)
            except Exception:
                return await ctx.send("❌ Invalid color. Use hex (e.g. #7289da)")
        if title:
            event_conf["title"] = title
        with open(MODLOGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        await ctx.send(f"✅ Embed config updated for `{event}`.")

    @commands.command(name="logembedreset", help="Reset embed customization for a specific event type.")
    @commands.has_permissions(administrator=True)
    async def logembedreset(self, ctx, event: str):
        try:
            with open(MODLOGS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        conf = data.setdefault(str(ctx.guild.id), {})
        event_embeds = conf.setdefault("event_embeds", {})
        if event in event_embeds:
            del event_embeds[event]
        with open(MODLOGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        await ctx.send(f"♻️ Embed config reset for `{event}`.")
    # Member banned
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await log_mod_action(guild, "ban", user, user, "User was banned from the server.")

    # Member unbanned
    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        await log_mod_action(guild, "unban", user, user, "User was unbanned from the server.")

    # Member update (nickname, roles)
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Nickname change
        if before.nick != after.nick:
            await log_mod_action(after.guild, "nickname", after, after, f"Nickname changed: {before.nick} → {after.nick}")
        # Role changes
        if set(before.roles) != set(after.roles):
            before_roles = set(before.roles)
            after_roles = set(after.roles)
            added = after_roles - before_roles
            removed = before_roles - after_roles
            if added:
                await log_mod_action(after.guild, "roleadd", after, after, f"Roles added: {', '.join(r.name for r in added)}")
            if removed:
                await log_mod_action(after.guild, "roleremove", after, after, f"Roles removed: {', '.join(r.name for r in removed)}")
        # Boost/unboost
        if before.premium_since != after.premium_since:
            if after.premium_since:
                await log_mod_action(after.guild, "boost", after, after, f"Started boosting the server!")
            else:
                await log_mod_action(after.guild, "unboost", after, after, f"Stopped boosting the server.")
        # Timeout
        if getattr(before, 'timed_out_until', None) != getattr(after, 'timed_out_until', None):
            if getattr(after, 'timed_out_until', None):
                await log_mod_action(after.guild, "timeout", after, after, f"Timed out until {after.timed_out_until}")
            else:
                await log_mod_action(after.guild, "untimeout", after, after, f"Timeout removed.")

    # Guild update (name, icon, etc)
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        changes = []
        if before.name != after.name:
            changes.append(f"Name: {before.name} → {after.name}")
        if before.icon != after.icon:
            changes.append("Icon changed.")
        if before.owner_id != after.owner_id:
            changes.append(f"Owner: <@{before.owner_id}> → <@{after.owner_id}>")
        if changes:
            await log_mod_action(after, "guild_update", after.me, after.me, " | ".join(changes))

    # Emoji events
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        before_set = set(e.id for e in before)
        after_set = set(e.id for e in after)
        added = [e for e in after if e.id not in before_set]
        removed = [e for e in before if e.id not in after_set]
        if added:
            await log_mod_action(guild, "emoji_add", guild.me, guild.me, f"Emojis added: {', '.join(e.name for e in added)}")
        if removed:
            await log_mod_action(guild, "emoji_remove", guild.me, guild.me, f"Emojis removed: {', '.join(e.name for e in removed)}")

    # Sticker events
    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):
        before_set = set(s.id for s in before)
        after_set = set(s.id for s in after)
        added = [s for s in after if s.id not in before_set]
        removed = [s for s in before if s.id not in after_set]
        if added:
            await log_mod_action(guild, "sticker_add", guild.me, guild.me, f"Stickers added: {', '.join(s.name for s in added)}")
        if removed:
            await log_mod_action(guild, "sticker_remove", guild.me, guild.me, f"Stickers removed: {', '.join(s.name for s in removed)}")

    # Invite events
    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        await log_mod_action(invite.guild, "invite_create", invite.inviter or invite.guild.me, invite.guild.me, f"Invite created: {invite.url}")

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        await log_mod_action(invite.guild, "invite_delete", invite.inviter or invite.guild.me, invite.guild.me, f"Invite deleted: {invite.url}")
    @commands.command(name="stoplogs", help="Stop logging all events.")
    @commands.has_permissions(administrator=True)
    async def stoplogs(self, ctx):
        try:
            with open(MODLOGS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        conf = data.setdefault(str(ctx.guild.id), {})
        conf["logging_enabled"] = False
        with open(MODLOGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        await ctx.send("🛑 Logging is now disabled for this server.")

    @commands.command(name="removelogs", help="Remove the log channel setting.")
    @commands.has_permissions(administrator=True)
    async def removelogs(self, ctx):
        try:
            with open(MODLOGS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        conf = data.setdefault(str(ctx.guild.id), {})
        conf.pop("log_channel", None)
        with open(MODLOGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        await ctx.send("❌ Log channel removed. Logging will not be sent to any channel until set again.")

    @commands.command(name="enablelog", help="Enable logging for a specific event type.")
    @commands.has_permissions(administrator=True)
    async def enablelog(self, ctx, event: str):
        try:
            with open(MODLOGS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        conf = data.setdefault(str(ctx.guild.id), {})
        enabled = set(conf.get("enabled_events", []))
        enabled.add(event)
        conf["enabled_events"] = list(enabled)
        with open(MODLOGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        await ctx.send(f"✅ Logging enabled for event: `{event}`.")

    @commands.command(name="disablelog", help="Disable logging for a specific event type.")
    @commands.has_permissions(administrator=True)
    async def disablelog(self, ctx, event: str):
        try:
            with open(MODLOGS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        conf = data.setdefault(str(ctx.guild.id), {})
        enabled = set(conf.get("enabled_events", []))
        if event in enabled:
            enabled.remove(event)
        conf["enabled_events"] = list(enabled)
        with open(MODLOGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        await ctx.send(f"🚫 Logging disabled for event: `{event}`.")

    @commands.command(name="logconfig", help="Show current log settings.")
    @commands.has_permissions(administrator=True)
    async def logconfig(self, ctx):
        try:
            with open(MODLOGS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        conf = data.get(str(ctx.guild.id), {})
        channel_id = conf.get("log_channel")
        enabled = conf.get("enabled_events", [])
        logging_enabled = conf.get("logging_enabled", True)
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        desc = f"**Log Channel:** {channel.mention if channel else 'Not set'}\n"
        desc += f"**Logging Enabled:** {logging_enabled}\n"
        desc += f"**Enabled Events:** {', '.join(enabled) if enabled else 'All'}"
        await ctx.send(embed=discord.Embed(title="Log Config", description=desc, color=discord.Color.blurple()))

    @commands.command(name="logembed", help="Customize log embed color and title.")
    @commands.has_permissions(administrator=True)
    async def logembed(self, ctx, color: Optional[str] = None, *, title: Optional[str] = None):
        try:
            with open(MODLOGS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        conf = data.setdefault(str(ctx.guild.id), {})
        if color:
            try:
                conf["embed_color"] = int(color.strip("#"), 16)
            except Exception:
                return await ctx.send("❌ Invalid color. Use hex (e.g. #7289da)")
        if title:
            conf["embed_title"] = title
        with open(MODLOGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        await ctx.send("✅ Log embed updated.")
    @commands.command(name="setlogs", help="Set the channel for all event logs.")
    @commands.has_permissions(administrator=True)
    async def setlogs(self, ctx, channel: Optional[discord.TextChannel] = None):
        """
        Set the channel for all event logs. Usage: setlogs #channel
        """
        if channel is None:
            channel = ctx.channel if isinstance(ctx.channel, discord.TextChannel) else None
        if channel is None:
            await ctx.send("❌ Please specify a text channel.")
            return
        # Load or create modlogs.json
        try:
            with open(MODLOGS_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {}
        data[str(ctx.guild.id)] = {"log_channel": channel.id}
        with open(MODLOGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        await ctx.send(f"✅ Log channel set to {channel.mention} for all events.")
    def __init__(self, bot):
        self.bot = bot

    # When bot is ready
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} is now online!")
        try:
            synced = await self.bot.tree.sync()
            print(f"✅ Synced {len(synced)} slash commands.")
        except Exception as e:
            print(f"❌ Failed to sync commands: {e}")

    # Member joins
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Use member as both moderator and target if needed
        await log_mod_action(member.guild, "member_join", member, member, "Joined the server")

    # Member leaves
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await log_mod_action(member.guild, "member_leave", member, member, "Left the server")

    # Message deleted
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        await log_mod_action(message.guild, "message_delete", message.author, message.author, f"Deleted message: `{message.content}`")

    # Message edited
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        await log_mod_action(before.guild, "message_edit", before.author, before.author,
                             f"Edited message:\n**Before:** {before.content}\n**After:** {after.content}")

    # Channel created
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        # Use the bot's member as dummy moderator if available
        bot_member = channel.guild.get_member(self.bot.user.id) if hasattr(self, 'bot') and self.bot.user else None
        if bot_member:
            await log_mod_action(channel.guild, "channel_create", bot_member, bot_member, f"Channel created: {channel.name}")

    # Channel deleted
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        bot_member = channel.guild.get_member(self.bot.user.id) if hasattr(self, 'bot') and self.bot.user else None
        if bot_member:
            await log_mod_action(channel.guild, "channel_delete", bot_member, bot_member, f"Channel deleted: {channel.name}")

    # Channel updated
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        bot_member = before.guild.get_member(self.bot.user.id) if hasattr(self, 'bot') and self.bot.user else None
        if bot_member:
            await log_mod_action(before.guild, "channel_update", bot_member, bot_member, f"Channel updated: {before.name}  {after.name}")

    # Role created
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        bot_member = role.guild.get_member(self.bot.user.id) if hasattr(self, 'bot') and self.bot.user else None
        if bot_member:
            await log_mod_action(role.guild, "role_create", bot_member, bot_member, f"Role created: {role.name}")

    # Role deleted
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        bot_member = role.guild.get_member(self.bot.user.id) if hasattr(self, 'bot') and self.bot.user else None
        if bot_member:
            await log_mod_action(role.guild, "role_delete", bot_member, bot_member, f"Role deleted: {role.name}")

    # Role updated
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        bot_member = before.guild.get_member(self.bot.user.id) if hasattr(self, 'bot') and self.bot.user else None
        if bot_member:
            await log_mod_action(before.guild, "role_update", bot_member, bot_member, f"Role updated: {before.name}  {after.name}")

async def setup(bot):
    await bot.add_cog(Events(bot))
