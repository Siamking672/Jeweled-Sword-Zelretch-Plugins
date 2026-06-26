"""Antiflood — auto-mute/kick/ban users who spam a chat."""

from __future__ import annotations

import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta

from pyrogram import filters
from pyrogram.types import ChatPermissions

from astralbot import on_command, on_event, help_menu, Config, db


__plugin_name__ = "Antiflood"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Auto-mute / kick / ban users who flood a chat."
__plugin_category__ = "utils"


# In-memory per-chat per-user message timestamps
_FLOOD_TRACKER: dict[tuple[int, int], list[float]] = defaultdict(list)


@on_command("antiflood", description="Configure antiflood (set <limit> / action <mute|kick|ban> / off).", permission="sudo", admin_only=True, group_only=True)
async def antiflood_cmd(client, message):
    if len(message.command) < 3:
        cfg = await db.get("antiflood", {"_id": message.chat.id}) or {}
        return await message.edit_text(
            f"**Antiflood config for this chat**\n"
            f"  Limit: `{cfg.get('limit', 5)}` msgs / 5 sec\n"
            f"  Action: `{cfg.get('action', 'mute')}`\n"
            f"\n"
            f"Usage:\n"
            f"  `{Config.primary_prefix}antiflood set <limit>` — set message limit\n"
            f"  `{Config.primary_prefix}antiflood action <mute|kick|ban>`\n"
            f"  `{Config.primary_prefix}antiflood off` — disable"
        )
    sub = message.command[1].lower()
    arg = message.command[2].lower()
    chat_id = message.chat.id

    if sub == "set":
        try:
            limit = int(arg)
        except ValueError:
            return await message.edit_text("Limit must be an integer.")
        cfg = await db.get("antiflood", {"_id": chat_id}) or {}
        cfg.update({"_id": chat_id, "limit": limit})
        await db.insert("antiflood", cfg)
        await message.edit_text(f"✅ Antiflood limit: `{limit}` msgs / 5 sec.")
    elif sub == "action":
        if arg not in ("mute", "kick", "ban"):
            return await message.edit_text("Action must be mute, kick, or ban.")
        cfg = await db.get("antiflood", {"_id": chat_id}) or {}
        cfg.update({"_id": chat_id, "action": arg})
        await db.insert("antiflood", cfg)
        await message.edit_text(f"✅ Antiflood action: `{arg}`.")
    elif sub == "off":
        await db.delete("antiflood", {"_id": chat_id})
        await message.edit_text("✅ Antiflood disabled.")
    else:
        await message.edit_text(f"Unknown subcommand. Use set / action / off.")


@on_event(filters.incoming & ~filters.service & ~filters.bot)
async def antiflood_watcher(client, message):
    """Track message timestamps and apply the configured action on flood."""
    if not message.from_user:
        return
    chat_id = message.chat.id
    user_id = message.from_user.id

    cfg = await db.get("antiflood", {"_id": chat_id})
    if not cfg:
        return
    limit = cfg.get("limit", 5)
    action = cfg.get("action", "mute")

    now = time.time()
    key = (chat_id, user_id)
    times = _FLOOD_TRACKER[key]
    # Keep only messages from the last 5 seconds
    cutoff = now - 5
    times[:] = [t for t in times if t > cutoff]
    times.append(now)

    if len(times) > limit:
        # Flood detected
        del _FLOOD_TRACKER[key]
        try:
            if action == "mute":
                until = datetime.now(timezone.utc) + timedelta(minutes=30)
                await client.restrict_chat_member(
                    chat_id, user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until,
                )
                verb = "muted for 30 min"
            elif action == "kick":
                await client.ban_chat_member(chat_id, user_id)
                await client.unban_chat_member(chat_id, user_id)
                verb = "kicked"
            elif action == "ban":
                await client.ban_chat_member(chat_id, user_id)
                verb = "banned"
            else:
                return
            try:
                await message.reply_text(
                    f"🛑 Antiflood: {message.from_user.mention} has been {verb} for flooding."
                )
            except Exception:
                pass
        except Exception:
            pass


help_menu.add(
    command="antiflood",
    args="set <limit> | action <mute|kick|ban> | off",
    description="Configure antiflood protection in this chat.",
    example=".antiflood set 5",
    category="utils",
    plugin="antiflood",
).register()
