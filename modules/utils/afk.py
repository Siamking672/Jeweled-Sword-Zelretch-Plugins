"""AFK — set yourself away with auto-reply and auto-unset on activity."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from pyrogram import filters

from astralbot import on_command, on_event, help_menu, Config, db
from astralbot.helpers.formatting import mention_user


__plugin_name__ = "AFK"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Set yourself away with auto-reply to mentions and auto-unset on activity."
__plugin_category__ = "utils"


COLLECTION = "afk"


@on_command("afk", description="Mark yourself as AFK.", permission="sudo")
async def afk_cmd(client, message):
    reason = " ".join(message.command[1:]) if len(message.command) > 1 else "No reason."
    now = time.time()
    await db.insert(COLLECTION, {
        "_id": "me",
        "user_id": message.from_user.id if message.from_user else 0,
        "reason": reason,
        "since": now,
    })
    await message.edit_text(f"💤 You are now AFK.\nReason: {reason}")


@on_command("unafk", description="Manually clear AFK status.", permission="sudo")
async def unafk_cmd(client, message):
    await db.delete(COLLECTION, {"_id": "me"})
    await message.edit_text("✅ Welcome back! AFK cleared.")


@on_event(filters.outgoing & ~filters.service)
async def afk_unset_watcher(client, message):
    """Auto-clear AFK when the user sends any message."""
    afk = await db.get(COLLECTION, {"_id": "me"})
    if not afk:
        return
    await db.delete(COLLECTION, {"_id": "me"})
    try:
        await message.reply_text("✅ Welcome back! AFK cleared.")
    except Exception:
        pass


@on_event(filters.mentioned & filters.incoming)
async def afk_reply_watcher(client, message):
    """Auto-reply when someone mentions the AFK user."""
    afk = await db.get(COLLECTION, {"_id": "me"})
    if not afk:
        return
    since = datetime.fromtimestamp(afk["since"], tz=timezone.utc)
    elapsed = int(time.time() - afk["since"])
    elapsed_str = (
        f"{elapsed // 3600}h {(elapsed % 3600) // 60}m {elapsed % 60}s"
        if elapsed >= 3600
        else f"{elapsed // 60}m {elapsed % 60}s"
        if elapsed >= 60
        else f"{elapsed}s"
    )
    try:
        await message.reply_text(
            f"💤 **{message.chat.me.first_name if hasattr(message.chat, 'me') else 'User'} is AFK.**\n"
            f"Since: `{since.strftime('%Y-%m-%d %H:%M UTC')}` (`{elapsed_str} ago`)\n"
            f"Reason: {afk.get('reason', 'No reason.')}"
        )
    except Exception:
        pass


for cmd, args, desc, ex in [
    ("afk", "[reason]", "Mark yourself as AFK.", ".afk sleeping"),
    ("unafk", None, "Manually clear AFK status.", ".unafk"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="utils",
        plugin="afk",
    ).register()
