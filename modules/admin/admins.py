"""Admin commands — promote, demote, ban, kick, mute, pin.

Ports the strongest commands from Zelretch's user/admins.py and
CustomModules' chatmodule.py into a unified, manifest-driven plugin.
"""

from __future__ import annotations

from pyrogram import filters

from astralbot import on_command, help_menu, Config
from astralbot.helpers.admin import is_user_admin, can_restrict_members
from astralbot.helpers.formatting import mention_user

__plugin_name__ = "Admin Tools"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Group administration: promote, demote, ban, kick, mute, pin."
__plugin_category__ = "admin"


async def _get_target_user(client, message) -> tuple[int, str] | None:
    """Extract (user_id, first_name) from reply or command arg."""
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        return u.id, u.first_name or "User"
    if len(message.command) >= 2:
        try:
            uid = int(message.command[1])
            try:
                user = await client.get_users(uid)
                return user.id, user.first_name or "User"
            except Exception:
                return uid, f"User {uid}"
        except ValueError:
            pass
    return None


@on_command("promote", description="Promote a user to admin.", permission="sudo", admin_only=True, group_only=True)
async def promote_cmd(client, message):
    target = await _get_target_user(client, message)
    if not target:
        return await message.edit_text(f"Reply to a user or use `{Config.primary_prefix}promote <id>`")
    uid, name = target
    try:
        await client.promote_chat_member(message.chat.id, uid)
        await message.edit_text(f"✅ Promoted {mention_user(uid, name)} in {message.chat.title or 'this chat'}.")
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


@on_command("demote", description="Demote an admin.", permission="sudo", admin_only=True, group_only=True)
async def demote_cmd(client, message):
    target = await _get_target_user(client, message)
    if not target:
        return await message.edit_text(f"Reply to a user or use `{Config.primary_prefix}demote <id>`")
    uid, name = target
    try:
        await client.promote_chat_member(
            message.chat.id, uid,
            is_anonymous=False,
            can_manage_chat=False,
            can_change_info=False,
            can_post_messages=False,
            can_edit_messages=False,
            can_delete_messages=False,
            can_invite_users=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_promote_members=False,
            can_manage_video_chats=False,
        )
        await message.edit_text(f"✅ Demoted {mention_user(uid, name)}.")
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


@on_command("ban", description="Ban a user from the chat.", permission="sudo", admin_only=True, group_only=True)
async def ban_cmd(client, message):
    target = await _get_target_user(client, message)
    if not target:
        return await message.edit_text(f"Reply to a user or use `{Config.primary_prefix}ban <id>`")
    uid, name = target
    reason = " ".join(message.command[2:]) if len(message.command) > 2 else None
    try:
        await client.ban_chat_member(message.chat.id, uid)
        msg = f"✅ Banned {mention_user(uid, name)}"
        if reason:
            msg += f"\nReason: {reason}"
        await message.edit_text(msg)
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


@on_command("unban", description="Unban a user.", permission="sudo", admin_only=True, group_only=True)
async def unban_cmd(client, message):
    target = await _get_target_user(client, message)
    if not target:
        return await message.edit_text(f"Reply to a user or use `{Config.primary_prefix}unban <id>`")
    uid, name = target
    try:
        await client.unban_chat_member(message.chat.id, uid)
        await message.edit_text(f"✅ Unbanned {mention_user(uid, name)}.")
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


@on_command("kick", description="Kick a user from the chat.", permission="sudo", admin_only=True, group_only=True)
async def kick_cmd(client, message):
    target = await _get_target_user(client, message)
    if not target:
        return await message.edit_text(f"Reply to a user or use `{Config.primary_prefix}kick <id>`")
    uid, name = target
    try:
        await client.ban_chat_member(message.chat.id, uid)
        await client.unban_chat_member(message.chat.id, uid)
        await message.edit_text(f"✅ Kicked {mention_user(uid, name)}.")
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


@on_command("mute", description="Mute a user (restrict sending messages).", permission="sudo", admin_only=True, group_only=True)
async def mute_cmd(client, message):
    target = await _get_target_user(client, message)
    if not target:
        return await message.edit_text(f"Reply to a user or use `{Config.primary_prefix}mute <id>`")
    uid, name = target
    try:
        from datetime import datetime, timezone, timedelta
        from pyrogram.types import ChatPermissions
        # Default 1 hour; user can pass minutes as arg
        minutes = int(message.command[2]) if len(message.command) > 2 else 60
        until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        await client.restrict_chat_member(
            message.chat.id, uid,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until,
        )
        await message.edit_text(f"🔇 Muted {mention_user(uid, name)} for {minutes} min.")
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


@on_command("unmute", description="Unmute a user.", permission="sudo", admin_only=True, group_only=True)
async def unmute_cmd(client, message):
    target = await _get_target_user(client, message)
    if not target:
        return await message.edit_text(f"Reply to a user or use `{Config.primary_prefix}unmute <id>`")
    uid, name = target
    try:
        from pyrogram.types import ChatPermissions
        await client.restrict_chat_member(
            message.chat.id, uid,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await message.edit_text(f"🔊 Unmuted {mention_user(uid, name)}.")
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


@on_command("pin", description="Pin the replied message.", permission="sudo", admin_only=True, group_only=True)
async def pin_cmd(client, message):
    if not message.reply_to_message:
        return await message.edit_text("Reply to a message to pin it.")
    notify = "loud" in (message.text or "").lower()
    try:
        await client.pin_chat_message(
            message.chat.id, message.reply_to_message.id, disable_notification=not notify
        )
        await message.edit_text("📌 Pinned.")
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


@on_command("unpin", description="Unpin the replied message.", permission="sudo", admin_only=True, group_only=True)
async def unpin_cmd(client, message):
    if not message.reply_to_message:
        return await message.edit_text("Reply to a pinned message to unpin it.")
    try:
        await client.unpin_chat_message(message.chat.id, message.reply_to_message.id)
        await message.edit_text("📍 Unpinned.")
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


@on_command("id", description="Get the ID of the chat or replied user.", permission="public")
async def id_cmd(client, message):
    chat_id = message.chat.id
    chat_title = message.chat.title or message.chat.first_name or "this chat"
    text = f"🆔 **Chat:** `{chat_title}` (`{chat_id}`)"
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        text += f"\n👤 **User:** {mention_user(u.id, u.first_name)} (`{u.id}`)"
    await message.edit_text(text)


# Register help entries
for cmd, args, desc, ex in [
    ("promote", "<reply|id>", "Promote a user to admin.", ".promote (reply)"),
    ("demote", "<reply|id>", "Demote an admin.", ".demote (reply)"),
    ("ban", "<reply|id> [reason]", "Ban a user.", ".ban spammer"),
    ("unban", "<reply|id>", "Unban a user.", ".unban 12345"),
    ("kick", "<reply|id>", "Kick a user.", ".kick (reply)"),
    ("mute", "<reply|id> [minutes]", "Mute a user (default 60 min).", ".mute 30"),
    ("unmute", "<reply|id>", "Unmute a user.", ".unmute (reply)"),
    ("pin", "<reply>", "Pin the replied message.", ".pin (reply)"),
    ("unpin", "<reply>", "Unpin the replied message.", ".unpin (reply)"),
    ("id", None, "Get chat / user ID.", ".id"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="admin",
        plugin="admins",
    ).register()
