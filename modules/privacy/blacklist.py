"""Blacklist — chat-local word blacklist with auto-delete."""

from __future__ import annotations

import re

from pyrogram import filters

from astralbot import on_command, on_event, help_menu, Config, db


__plugin_name__ = "Blacklist"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Chat-local word blacklist with auto-delete on match."
__plugin_category__ = "privacy"


COLLECTION = "blacklist"


@on_command("bl", description="Add a word to the chat blacklist.", permission="sudo", admin_only=True, group_only=True)
async def bl_add_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}bl <word>`")
    word = " ".join(message.command[1:]).lower()
    chat_id = message.chat.id
    await db.insert(COLLECTION, {
        "_id": f"{chat_id}:{word}",
        "chat_id": chat_id,
        "word": word,
    })
    await message.edit_text(f"✅ Blacklisted `{word}` in this chat.")


@on_command("unbl", description="Remove a word from the blacklist.", permission="sudo", admin_only=True, group_only=True)
async def bl_rm_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}unbl <word>`")
    word = " ".join(message.command[1:]).lower()
    deleted = await db.delete(COLLECTION, {"chat_id": message.chat.id, "word": word})
    if deleted:
        await message.edit_text(f"🗑️ Removed `{word}` from blacklist.")
    else:
        await message.edit_text(f"❌ `{word}` was not blacklisted.")


@on_command("blist", description="List blacklisted words in this chat.", permission="sudo", group_only=True)
async def bl_list_cmd(client, message):
    items = await db.find(COLLECTION, {"chat_id": message.chat.id})
    if not items:
        return await message.edit_text("No blacklisted words in this chat.")
    words = sorted(i["word"] for i in items)
    await message.edit_text(
        f"**Blacklist for {message.chat.title or 'this chat'}:**\n"
        + "\n".join(f"  • `{w}`" for w in words)
    )


@on_event(filters.incoming & ~filters.service & filters.text & ~filters.me)
async def blacklist_watcher(client, message):
    """Auto-delete messages containing blacklisted words."""
    if not message.text:
        return
    chat_id = message.chat.id
    items = await db.find(COLLECTION, {"chat_id": chat_id})
    if not items:
        return
    text_lower = message.text.lower()
    for item in items:
        if item["word"] in text_lower:
            try:
                await message.delete()
            except Exception:
                pass
            return


for cmd, args, desc, ex in [
    ("bl", "<word>", "Blacklist a word.", ".bl spam"),
    ("unbl", "<word>", "Remove a blacklisted word.", ".unbl spam"),
    ("blist", None, "List blacklisted words.", ".blist"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="privacy",
        plugin="blacklist",
    ).register()
