"""Purge — delete ranges of messages, or all messages from a user."""

from __future__ import annotations

import asyncio

from astralbot import on_command, help_menu, Config
from astralbot.helpers.admin import can_delete_messages


__plugin_name__ = "Purge"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Delete ranges of messages or all messages from a user."
__plugin_category__ = "admin"


@on_command("purge", description="Purge messages from reply up to this message.", permission="sudo", admin_only=True, group_only=True)
async def purge_cmd(client, message):
    if not message.reply_to_message:
        return await message.edit_text("Reply to the first message to purge from.")
    start_id = message.reply_to_message.id
    end_id = message.id
    if end_id <= start_id:
        return await message.edit_text("Reply to an earlier message.")

    msg = await message.edit_text("🧹 Purging...")
    deleted = 0
    batch: list[int] = []
    for mid in range(start_id, end_id + 1):
        batch.append(mid)
        if len(batch) >= 100:
            try:
                await client.delete_messages(message.chat.id, batch)
                deleted += len(batch)
            except Exception:
                pass
            batch.clear()
            await asyncio.sleep(0.5)
    if batch:
        try:
            await client.delete_messages(message.chat.id, batch)
            deleted += len(batch)
        except Exception:
            pass
    await msg.edit_text(f"🧹 Purged `{deleted}` messages.")
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass


@on_command("del", description="Delete the replied message.", permission="sudo", admin_only=True, group_only=True)
async def del_cmd(client, message):
    if not message.reply_to_message:
        return await message.edit_text("Reply to a message to delete it.")
    try:
        await client.delete_messages(message.chat.id, [message.reply_to_message.id, message.id])
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


@on_command("purgeuser", description="Purge all messages from a user (last 1000).", permission="sudo", admin_only=True, group_only=True)
async def purgeuser_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.edit_text("Reply to a message from the user to purge.")
    target_uid = message.reply_to_message.from_user.id
    msg = await message.edit_text(f"🧹 Purging messages from user `{target_uid}`...")
    deleted = 0
    async for m in client.get_chat_history(message.chat.id, limit=1000):
        if m.from_user and m.from_user.id == target_uid:
            try:
                await m.delete()
                deleted += 1
            except Exception:
                pass
    await msg.edit_text(f"🧹 Purged `{deleted}` messages from user `{target_uid}`.")
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass


for cmd, args, desc, ex in [
    ("purge", "<reply>", "Purge messages from reply to here.", ".purge (reply)"),
    ("del", "<reply>", "Delete the replied message.", ".del (reply)"),
    ("purgeuser", "<reply>", "Purge all messages from a user (last 1000).", ".purgeuser (reply)"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="admin",
        plugin="purge",
    ).register()
