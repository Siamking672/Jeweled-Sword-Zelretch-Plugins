"""Antichannel — auto-delete messages from anonymous channel admins."""

from __future__ import annotations

from pyrogram import filters

from astralbot import on_command, on_event, help_menu, Config, db


__plugin_name__ = "Antichannel"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Auto-delete messages sent via anonymous channel admins."
__plugin_category__ = "privacy"


@on_command("antichannel", description="Toggle antichannel for the current chat.", permission="sudo", admin_only=True, group_only=True)
async def antichannel_cmd(client, message):
    chat_id = message.chat.id
    doc = await db.get("antichannel", {"_id": chat_id})
    if doc:
        await db.delete("antichannel", {"_id": chat_id})
        await message.edit_text("✅ Antichannel disabled for this chat.")
    else:
        await db.insert("antichannel", {"_id": chat_id, "chat_id": chat_id})
        await message.edit_text("✅ Antichannel enabled for this chat.")


@on_event(filters.group & filters.incoming)
async def antichannel_watcher(client, message):
    """Auto-delete messages from anonymous channel senders."""
    if not message.sender_chat:
        return
    if message.sender_chat.type != "channel":
        return
    chat_id = message.chat.id
    doc = await db.get("antichannel", {"_id": chat_id})
    if not doc:
        return
    try:
        await message.delete()
    except Exception:
        pass


help_menu.add(
    command="antichannel",
    args=None,
    description="Toggle antichannel for the current chat.",
    example=".antichannel",
    category="privacy",
    plugin="antichannel",
).register()
