"""PM permit — auto-warn and block unsolicited PMs.

Inspired by Zelretch's user/pmpermit.py — but with the HellBot user-facing
strings replaced and a configurable warning template.
"""

from __future__ import annotations

import time

from pyrogram import filters

from astralbot import on_command, on_event, help_menu, Config, db


__plugin_name__ = "PM Permit"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Auto-warn and block unsolicited private messages."
__plugin_category__ = "privacy"


COLLECTION = "pmpermit"


async def _is_approved(user_id: int) -> bool:
    doc = await db.get(COLLECTION, {"_id": f"approved:{user_id}"})
    return doc is not None


async def _approve(user_id: int) -> None:
    await db.insert(COLLECTION, {"_id": f"approved:{user_id}", "user_id": user_id})


async def _revoke(user_id: int) -> None:
    await db.delete(COLLECTION, {"_id": f"approved:{user_id}"})
    await db.delete(COLLECTION, {"_id": f"warns:{user_id}"})


async def _get_warn_count(user_id: int) -> int:
    doc = await db.get(COLLECTION, {"_id": f"warns:{user_id}"})
    return doc["count"] if doc else 0


async def _inc_warn(user_id: int) -> int:
    cur = await _get_warn_count(user_id)
    new = cur + 1
    await db.insert(COLLECTION, {"_id": f"warns:{user_id}", "user_id": user_id, "count": new})
    return new


async def _reset_warns(user_id: int) -> None:
    await db.delete(COLLECTION, {"_id": f"warns:{user_id}"})


@on_command("approve", description="Approve a user to PM you.", permission="sudo")
async def approve_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        if len(message.command) < 2:
            return await message.edit_text("Reply to a user or specify an ID.")
        try:
            uid = int(message.command[1])
        except ValueError:
            return await message.edit_text("Invalid user ID.")
    else:
        uid = message.reply_to_message.from_user.id
    await _approve(uid)
    await _reset_warns(uid)
    await message.edit_text(f"✅ Approved `{uid}` to PM you.")


@on_command(["disapprove", "revoke"], description="Revoke PM approval for a user.", permission="sudo")
async def disapprove_cmd(client, message):
    if not message.reply_to_message or not message.reply_to_message.from_user:
        if len(message.command) < 2:
            return await message.edit_text("Reply to a user or specify an ID.")
        try:
            uid = int(message.command[1])
        except ValueError:
            return await message.edit_text("Invalid user ID.")
    else:
        uid = message.reply_to_message.from_user.id
    await _revoke(uid)
    await message.edit_text(f"🗑️ Revoked PM approval for `{uid}`.")


@on_command("approved", description="List approved PM users.", permission="sudo")
async def approved_cmd(client, message):
    docs = await db.find(COLLECTION, {})
    approved = [d["user_id"] for d in docs if d["_id"].startswith("approved:")]
    if not approved:
        return await message.edit_text("No approved users.")
    lines = ["**Approved PM users:**\n"]
    for uid in approved:
        lines.append(f"  • `{uid}`")
    await message.edit_text("\n".join(lines))


@on_event(filters.incoming & filters.private & ~filters.service & ~filters.bot)
async def pmpermit_watcher(client, message):
    """Auto-warn / block unsolicited PMs."""
    if not message.from_user:
        return
    sender = message.from_user.id
    # Owner and sudo always pass
    if Config.is_privileged(sender):
        return
    if await _is_approved(sender):
        return
    # Otherwise increment warn count
    count = await _inc_warn(sender)
    max_warns = await db.get_env("PM_MAX_SPAM", default=3)
    try:
        max_warns = int(max_warns)
    except (TypeError, ValueError):
        max_warns = 3

    template = await db.get_env(
        "PM_TEMPLATE",
        default=(
            "👋 Hello! This is a private account.\n"
            "Please wait — I'll respond when I'm available.\n"
            "Spam will be auto-blocked. Warn: {count}/{max}"
        ),
    )

    if count >= max_warns:
        try:
            await message.reply_text("🚫 You've been blocked for spamming. Goodbye.")
            await client.block_user(sender)
        except Exception:
            pass
        return
    try:
        await message.reply_text(template.format(count=count, max=max_warns))
    except Exception:
        pass


for cmd, args, desc, ex in [
    ("approve", "<reply|id>", "Approve a user to PM you.", ".approve (reply)"),
    ("disapprove", "<reply|id>", "Revoke PM approval.", ".disapprove (reply)"),
    ("approved", None, "List approved users.", ".approved"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="privacy",
        plugin="pmpermit",
    ).register()
