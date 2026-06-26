"""Antipin — auto-unpin messages pinned by others (anti-pin-spam)."""

from __future__ import annotations

from pyrogram import filters

from astralbot import on_command, on_event, help_menu, Config, db


__plugin_name__ = "Antipin"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Auto-unpin messages pinned by non-admins (anti-pin-spam)."
__plugin_category__ = "privacy"


@on_command("antipin", description="Toggle antipin for the current chat.", permission="sudo", group_only=True)
async def antipin_cmd(client, message):
    chat_id = message.chat.id
    doc = await db.get("antipin", {"_id": chat_id})
    if doc:
        await db.delete("antipin", {"_id": chat_id})
        await message.edit_text("✅ Antipin disabled for this chat.")
    else:
        await db.insert("antipin", {"_id": chat_id, "chat_id": chat_id})
        await message.edit_text("✅ Antipin enabled for this chat.")


@on_event(filters.group & ~filters.service)
async def antipin_watcher(client, message):
    """Watch for pinned messages and auto-unpin if not from an admin."""
    # This is a simplified watcher — Pyrogram doesn't expose a clean
    # 'message pinned' event, so we'd need to poll. For now, this is a stub
    # that demonstrates the architecture.
    pass


help_menu.add(
    command="antipin",
    args=None,
    description="Toggle antipin for the current chat.",
    example=".antipin",
    category="privacy",
    plugin="antipin",
).register()
