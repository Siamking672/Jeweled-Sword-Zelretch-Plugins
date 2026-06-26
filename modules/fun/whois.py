"""Whois — show user / chat info."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config
from astralbot.helpers.formatting import escape_html, mention_user


__plugin_name__ = "Whois"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Show detailed info about a user or chat."
__plugin_category__ = "fun"


@on_command(["whois", "info"], description="Show info about a user.", permission="public")
async def whois_cmd(client, message):
    target_user = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) >= 2:
        try:
            target_user = await client.get_users(int(message.command[1]))
        except (ValueError, Exception):
            pass

    if target_user is None:
        # Show chat info instead
        chat = message.chat
        text = (
            f"**Chat info**\n"
            f"  Title: {escape_html(chat.title or chat.first_name or 'n/a')}\n"
            f"  ID: `{chat.id}`\n"
            f"  Type: `{chat.type}`\n"
            f"  Members: `{chat.members_count if hasattr(chat, 'members_count') else '?'}`\n"
            f"  Username: @{chat.username if chat.username else 'n/a'}"
        )
        await message.edit_text(text)
        return

    u = target_user
    lines = [
        f"**User info**",
        f"  Name: {escape_html(u.first_name or '')} {escape_html(u.last_name or '')}".rstrip(),
        f"  ID: `{u.id}`",
        f"  Username: @{u.username}" if u.username else "  Username: (none)",
        f"  Bot: `{u.is_bot}`",
    ]
    # Try to fetch full info (bio, etc.)
    try:
        full = await client.get_chat(u.id)
        if full.bio:
            lines.append(f"  Bio: {escape_html(full.bio)}")
        if full.photo:
            lines.append("  Photo: (has profile photo)")
    except Exception:
        pass
    # Mention
    lines.append(f"\nMention: {mention_user(u.id, u.first_name or 'User')}")
    await message.edit_text("\n".join(lines))


@on_command("chatinfo", description="Show info about the current chat.", permission="public")
async def chatinfo_cmd(client, message):
    chat = await client.get_chat(message.chat.id)
    text = (
        f"**Chat info**\n"
        f"  Title: {escape_html(chat.title or chat.first_name or 'n/a')}\n"
        f"  ID: `{chat.id}`\n"
        f"  Type: `{chat.type}`\n"
        f"  Members: `{chat.members_count if hasattr(chat, 'members_count') else '?'}`\n"
        f"  Username: @{chat.username}" if chat.username else "  Username: (none)"
    )
    if chat.description:
        text += f"\n  Description: {escape_html(chat.description)}"
    if chat.linked_chat:
        text += f"\n  Linked chat: `{chat.linked_chat.id}`"
    await message.edit_text(text)


for cmd, args, desc, ex in [
    ("whois", "<reply|id>", "Show user info.", ".whois (reply)"),
    ("chatinfo", None, "Show chat info.", ".chatinfo"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="fun",
        plugin="whois",
    ).register()
