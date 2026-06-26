"""Snips — chat-local command shortcuts (trigger → reply text)."""

from __future__ import annotations

from pyrogram import filters

from astralbot import on_command, on_event, help_menu, Config, db


__plugin_name__ = "Snips"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Chat-local command shortcuts: trigger word → reply text."
__plugin_category__ = "utils"


COLLECTION = "snips"


@on_command("snip", description="Save a chat-local snip.", permission="sudo")
async def snip_cmd(client, message):
    raw = message.text or ""
    parts = raw.split(None, 2)
    if len(parts) < 3:
        return await message.edit_text(
            f"Usage: `{Config.primary_prefix}snip <name> <content>`"
        )
    name = parts[1].lower()
    content = parts[2]
    chat_id = message.chat.id
    await db.insert(COLLECTION, {
        "_id": f"{chat_id}:{name}",
        "chat_id": chat_id,
        "name": name,
        "content": content,
    })
    await message.edit_text(f"✂️ Saved snip `{name}` for this chat.")


@on_command("snips", description="List all snips in this chat.", permission="sudo")
async def snips_cmd(client, message):
    snips = await db.find(COLLECTION, {"chat_id": message.chat.id})
    if not snips:
        return await message.edit_text("No snips in this chat.")
    lines = ["**Snips in this chat:**\n"]
    for s in sorted(snips, key=lambda x: x["name"]):
        preview = s["content"][:50].replace("\n", " ")
        if len(s["content"]) > 50:
            preview += "..."
        lines.append(f"  • `{s['name']}` — {preview}")
    await message.edit_text("\n".join(lines))


@on_command("rmsnip", description="Delete a snip.", permission="sudo")
async def rmsnip_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}rmsnip <name>`")
    name = message.command[1].lower()
    deleted = await db.delete(COLLECTION, {"chat_id": message.chat.id, "name": name})
    if deleted:
        await message.edit_text(f"🗑️ Deleted snip `{name}`.")
    else:
        await message.edit_text(f"❌ No snip named `{name}`.")


@on_event(filters.incoming & ~filters.service & filters.text)
async def snip_trigger_watcher(client, message):
    """Watch for snip triggers — `.snipname` → reply with content."""
    if not message.text:
        return
    prefix = Config.primary_prefix if Config else "."
    if not message.text.startswith(prefix):
        return
    name = message.text[len(prefix):].split()[0].lower() if message.text[len(prefix):] else ""
    if not name:
        return
    snip = await db.get(COLLECTION, {"chat_id": message.chat.id, "name": name})
    if snip:
        try:
            await message.reply_text(snip["content"])
        except Exception:
            pass


for cmd, args, desc, ex in [
    ("snip", "<name> <content>", "Save a chat-local snip.", ".snip hi Hello!"),
    ("snips", None, "List all snips.", ".snips"),
    ("rmsnip", "<name>", "Delete a snip.", ".rmsnip hi"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="utils",
        plugin="snips",
    ).register()
