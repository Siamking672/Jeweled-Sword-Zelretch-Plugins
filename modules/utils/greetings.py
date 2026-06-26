"""Greetings — welcome / goodbye messages for new members."""

from __future__ import annotations

from pyrogram import filters

from astralbot import on_command, on_event, help_menu, Config, db
from astralbot.helpers.formatting import mention_user, escape_html


__plugin_name__ = "Greetings"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Welcome / goodbye messages for new chat members."
__plugin_category__ = "utils"


COLLECTION = "greetings"


@on_command("welcome", description="Set a welcome message (use {name} and {chat}).", permission="sudo", admin_only=True, group_only=True)
async def welcome_cmd(client, message):
    raw = message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2:
        return await message.edit_text(
            f"Usage: `{Config.primary_prefix}welcome <message>`\n"
            f"Placeholders: `{{name}}` `{{chat}}` `{{count}}`"
        )
    text = parts[1]
    await db.insert(COLLECTION, {
        "_id": f"{message.chat.id}:welcome",
        "chat_id": message.chat.id,
        "type": "welcome",
        "text": text,
    })
    await message.edit_text("👋 Welcome message saved.")


@on_command("goodbye", description="Set a goodbye message.", permission="sudo", admin_only=True, group_only=True)
async def goodbye_cmd(client, message):
    raw = message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}goodbye <message>`")
    text = parts[1]
    await db.insert(COLLECTION, {
        "_id": f"{message.chat.id}:goodbye",
        "chat_id": message.chat.id,
        "type": "goodbye",
        "text": text,
    })
    await message.edit_text("👋 Goodbye message saved.")


@on_command("nowelcome", description="Disable welcome message.", permission="sudo", admin_only=True, group_only=True)
async def nowelcome_cmd(client, message):
    await db.delete(COLLECTION, {"chat_id": message.chat.id, "type": "welcome"})
    await message.edit_text("👋 Welcome message disabled.")


@on_command("nogoodbye", description="Disable goodbye message.", permission="sudo", admin_only=True, group_only=True)
async def nogoodbye_cmd(client, message):
    await db.delete(COLLECTION, {"chat_id": message.chat.id, "type": "goodbye"})
    await message.edit_text("👋 Goodbye message disabled.")


@on_event(filters.new_chat_members)
async def welcome_watcher(client, message):
    greeting = await db.get(COLLECTION, {"chat_id": message.chat.id, "type": "welcome"})
    if not greeting:
        return
    for user in message.new_chat_members:
        name = user.first_name or "User"
        text = greeting["text"].format(
            name=mention_user(user.id, name),
            chat=escape_html(message.chat.title or "this chat"),
            count=message.chat.member_count if hasattr(message.chat, "member_count") else "?",
        )
        try:
            await message.reply_text(text)
        except Exception:
            pass


@on_event(filters.left_chat_member)
async def goodbye_watcher(client, message):
    greeting = await db.get(COLLECTION, {"chat_id": message.chat.id, "type": "goodbye"})
    if not greeting:
        return
    user = message.left_chat_member
    name = user.first_name if user else "User"
    text = greeting["text"].format(
        name=mention_user(user.id, name) if user else name,
        chat=escape_html(message.chat.title or "this chat"),
    )
    try:
        await message.reply_text(text)
    except Exception:
        pass


for cmd, args, desc, ex in [
    ("welcome", "<message>", "Set a welcome message.", ".welcome Hi {name}!"),
    ("goodbye", "<message>", "Set a goodbye message.", ".goodbye Bye {name}!"),
    ("nowelcome", None, "Disable welcome.", ".nowelcome"),
    ("nogoodbye", None, "Disable goodbye.", ".nogoodbye"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="utils",
        plugin="greetings",
    ).register()
