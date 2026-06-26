"""Lock / unlock — restrict chat media types.

Inspired by Zelretch's user/locker.py.
"""

from __future__ import annotations

from pyrogram.types import ChatPermissions

from astralbot import on_command, help_menu, Config


__plugin_name__ = "Lock"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Lock or unlock specific media types in a chat."
__plugin_category__ = "admin"


# Map lock-name -> (permission-attr-name, default value when locked)
LOCK_TYPES = {
    "messages": "can_send_messages",
    "media": "can_send_media_messages",
    "stickers": "can_send_other_messages",
    "gifs": "can_send_other_messages",
    "polls": "can_send_polls",
    "previews": "can_add_web_page_previews",
}


async def _get_current_permissions(client, chat_id):
    chat = await client.get_chat(chat_id)
    return chat.permissions


@on_command("lock", description="Lock a media type in this chat.", permission="sudo", admin_only=True, group_only=True)
async def lock_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(
            f"Usage: `{Config.primary_prefix}lock <{'|'.join(LOCK_TYPES)}>`"
        )
    what = message.command[1].lower()
    if what not in LOCK_TYPES:
        return await message.edit_text(
            f"Unknown type. Choose from: {', '.join(LOCK_TYPES)}"
        )
    perm_attr = LOCK_TYPES[what]
    try:
        current = await _get_current_permissions(client, message.chat.id)
        # Build new permissions: keep others, set this one to False
        perms_kwargs = {
            "can_send_messages": current.can_send_messages,
            "can_send_media_messages": current.can_send_media_messages,
            "can_send_other_messages": current.can_send_other_messages,
            "can_send_polls": getattr(current, "can_send_polls", False),
            "can_add_web_page_previews": current.can_add_web_page_previews,
        }
        # For 'messages' we just disable that one
        if what == "messages":
            perms_kwargs["can_send_messages"] = False
        elif what == "media":
            perms_kwargs["can_send_media_messages"] = False
        elif what in ("stickers", "gifs"):
            perms_kwargs["can_send_other_messages"] = False
        elif what == "polls":
            perms_kwargs["can_send_polls"] = False
        elif what == "previews":
            perms_kwargs["can_add_web_page_previews"] = False

        await client.set_chat_permissions(message.chat.id, ChatPermissions(**perms_kwargs))
        await message.edit_text(f"🔒 Locked `{what}` in this chat.")
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


@on_command("unlock", description="Unlock a media type in this chat.", permission="sudo", admin_only=True, group_only=True)
async def unlock_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(
            f"Usage: `{Config.primary_prefix}unlock <{'|'.join(LOCK_TYPES)}>`"
        )
    what = message.command[1].lower()
    if what not in LOCK_TYPES:
        return await message.edit_text(
            f"Unknown type. Choose from: {', '.join(LOCK_TYPES)}"
        )
    try:
        current = await _get_current_permissions(client, message.chat.id)
        perms_kwargs = {
            "can_send_messages": current.can_send_messages,
            "can_send_media_messages": current.can_send_media_messages,
            "can_send_other_messages": current.can_send_other_messages,
            "can_send_polls": getattr(current, "can_send_polls", False),
            "can_add_web_page_previews": current.can_add_web_page_previews,
        }
        if what == "messages":
            perms_kwargs["can_send_messages"] = True
        elif what == "media":
            perms_kwargs["can_send_media_messages"] = True
        elif what in ("stickers", "gifs"):
            perms_kwargs["can_send_other_messages"] = True
        elif what == "polls":
            perms_kwargs["can_send_polls"] = True
        elif what == "previews":
            perms_kwargs["can_add_web_page_previews"] = True

        await client.set_chat_permissions(message.chat.id, ChatPermissions(**perms_kwargs))
        await message.edit_text(f"🔓 Unlocked `{what}` in this chat.")
    except Exception as exc:
        await message.edit_text(f"❌ Failed: `{exc}`")


for cmd, args, desc, ex in [
    ("lock", "<type>", "Lock a media type in this chat.", ".lock media"),
    ("unlock", "<type>", "Unlock a media type in this chat.", ".unlock media"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="admin",
        plugin="lock",
    ).register()
