# utils/modutils.py
import discord, json, os
from discord.ext import commands
from typing import Optional

LOG_FILE = "data/modlogs.json"
MOD_ROLE_FILE = "data/modroles.json"

def load_json(file):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump({}, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

mod_roles = load_json(MOD_ROLE_FILE)
modlogs = load_json(LOG_FILE)

def is_mod_user(user: discord.Member):
    # Check if user has a mod role set by admin
    mod_roles = load_json("data/modroles.json").get(str(user.guild.id), [])
    has_mod_role = any(role.id in mod_roles for role in user.roles)
    # Check if user has any of the default Discord mod permissions
    perms = user.guild_permissions
    has_discord_mod_perm = perms.ban_members or perms.kick_members or perms.manage_messages or perms.moderate_members
    return has_mod_role or has_discord_mod_perm


from typing import Union
async def log_mod_action(guild: discord.Guild, action: str, moderator: discord.Member, target: Union[discord.Member, discord.User], reason: Optional[str]=None):
    entry = {
        "action": action,
        "moderator": str(moderator),
        "target": str(target),
        "reason": reason or "No reason provided",
        "timestamp": discord.utils.utcnow().isoformat()
    }
    # Save to logs (for history)
    logs = modlogs.setdefault(str(guild.id), [])
    logs.append(entry)
    save_json(LOG_FILE, modlogs)

    # Load config for this guild
    log_channel_id = None
    embed_color = discord.Color.red().value
    embed_title = "Mod Action"
    embed_icon = None
    logging_enabled = True
    enabled_events = None
    try:
        with open(LOG_FILE, "r") as f:
            logdata = json.load(f)
        conf = logdata.get(str(guild.id), {})
        log_channel_id = conf.get("log_channel")
        embed_color = conf.get("embed_color", embed_color)
        embed_title = conf.get("embed_title", embed_title)
        logging_enabled = conf.get("logging_enabled", True)
        enabled_events = conf.get("enabled_events")
        # Per-event embed customization
        event_embeds = conf.get("event_embeds", {})
        if action in event_embeds:
            econf = event_embeds[action]
            embed_color = econf.get("color", embed_color)
            embed_title = econf.get("title", embed_title)
            embed_icon = econf.get("icon")
    except Exception:
        pass
    # Check if logging is enabled and event is enabled
    if not logging_enabled:
        return
    if enabled_events is not None and action not in enabled_events:
        return
    channel = None
    if log_channel_id:
        channel = guild.get_channel(log_channel_id)
    if not channel:
        channel = discord.utils.get(guild.text_channels, name="mod-logs")
    if channel and isinstance(channel, discord.TextChannel):
        embed = discord.Embed(title=embed_title, color=embed_color)
        if embed_icon:
            embed.set_thumbnail(url=embed_icon)
        for k, v in entry.items():
            embed.add_field(name=k.title(), value=v, inline=False)
        await channel.send(embed=embed)
