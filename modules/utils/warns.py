"""Warns — chat-local warning system with thresholds and actions."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config, db
from astralbot.helpers.formatting import mention_user


__plugin_name__ = "Warns"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Chat-local warning system with configurable thresholds and actions."
__plugin_category__ = "utils"


COLLECTION = "warns"


async def _get_warn_count(chat_id: int, user_id: int) -> int:
    doc = await db.get(COLLECTION, {"_id": f"{chat_id}:{user_id}"})
    return doc["count"] if doc else 0


async def _inc_warn(chat_id: int, user_id: int) -> int:
    cur = await _get_warn_count(chat_id, user_id)
    new = cur + 1
    await db.insert(COLLECTION, {
        "_id": f"{chat_id}:{user_id}",
        "chat_id": chat_id,
        "user_id": user_id,
        "count": new,
    })
    return new


@on_command("warn", description="Warn a user (increment count).", permission="sudo", admin_only=True, group_only=True)
async def warn_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.edit_text("Reply to a user to warn them.")
    u = message.reply_to_message.from_user
    chat_id = message.chat.id
    count = await _inc_warn(chat_id, u.id)
    limit = 3  # configurable via .setvar WARN_LIMIT 5
    env_limit = await db.get_env("WARN_LIMIT", default=3)
    try:
        limit = int(env_limit)
    except (TypeError, ValueError):
        pass

    text = f"⚠️ {mention_user(u.id, u.first_name)} warned. Count: `{count}/{limit}`"
    if count >= limit:
        try:
            await client.ban_chat_member(chat_id, u.id)
            text += f"\n🚫 Auto-banned: reached limit of {limit}."
        except Exception as exc:
            text += f"\n❌ Auto-ban failed: `{exc}`"
    await message.edit_text(text)


@on_command("warns", description="Show a user's warn count in this chat.", permission="sudo", group_only=True)
async def warns_cmd(client, message):
    target_uid = None
    target_name = "User"
    if message.reply_to_message and message.reply_to_message.from_user:
        target_uid = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name or "User"
    elif len(message.command) >= 2:
        try:
            target_uid = int(message.command[1])
        except ValueError:
            pass
    if not target_uid:
        return await message.edit_text("Reply to a user or specify an ID.")
    count = await _get_warn_count(message.chat.id, target_uid)
    await message.edit_text(f"⚠️ {mention_user(target_uid, target_name)} has `{count}` warn(s) in this chat.")


@on_command("resetwarns", description="Reset a user's warn count.", permission="sudo", admin_only=True, group_only=True)
async def resetwarns_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        return await message.edit_text("Reply to a user.")
    u = message.reply_to_message.from_user
    await db.delete(COLLECTION, {"_id": f"{message.chat.id}:{u.id}"})
    await message.edit_text(f"✅ Reset warns for {mention_user(u.id, u.first_name)}.")


for cmd, args, desc, ex in [
    ("warn", "<reply>", "Warn a user (auto-ban at limit).", ".warn (reply)"),
    ("warns", "<reply|id>", "Show warn count.", ".warns (reply)"),
    ("resetwarns", "<reply>", "Reset warn count.", ".resetwarns (reply)"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="utils",
        plugin="warns",
    ).register()
