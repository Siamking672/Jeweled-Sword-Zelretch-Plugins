"""Notes — chat-local note storage. Get / set / list / delete."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config, db


__plugin_name__ = "Notes"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Chat-local note storage: save and retrieve text by keyword."
__plugin_category__ = "utils"


COLLECTION = "notes"


@on_command("note", description="Save a chat-local note.", permission="sudo")
async def note_cmd(client, message):
    # .note <name> <content>
    raw = message.text or ""
    parts = raw.split(None, 2)
    if len(parts) < 3:
        return await message.edit_text(
            f"Usage: `{Config.primary_prefix}note <name> <content>`"
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
    await message.edit_text(f"📝 Saved note `{name}` for this chat.")


@on_command("get", description="Retrieve a chat-local note.", permission="public")
async def get_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}get <name>`")
    name = message.command[1].lower()
    chat_id = message.chat.id
    note = await db.get(COLLECTION, {"chat_id": chat_id, "name": name})
    if not note:
        return await message.edit_text(f"❌ No note named `{name}` in this chat.")
    await message.edit_text(note["content"])


@on_command("notes", description="List all notes in this chat.", permission="public")
async def notes_cmd(client, message):
    chat_id = message.chat.id
    notes = await db.find(COLLECTION, {"chat_id": chat_id})
    if not notes:
        return await message.edit_text("No notes in this chat.")
    lines = [f"**Notes in {message.chat.title or 'this chat'}:**\n"]
    for n in sorted(notes, key=lambda x: x["name"]):
        preview = n["content"][:50].replace("\n", " ")
        if len(n["content"]) > 50:
            preview += "..."
        lines.append(f"  • `{n['name']}` — {preview}")
    await message.edit_text("\n".join(lines))


@on_command("rmnote", description="Delete a chat-local note.", permission="sudo")
async def rmnote_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}rmnote <name>`")
    name = message.command[1].lower()
    chat_id = message.chat.id
    deleted = await db.delete(COLLECTION, {"chat_id": chat_id, "name": name})
    if deleted:
        await message.edit_text(f"🗑️ Deleted note `{name}`.")
    else:
        await message.edit_text(f"❌ No note named `{name}`.")


for cmd, args, desc, ex in [
    ("note", "<name> <content>", "Save a chat-local note.", ".note wifi Password123"),
    ("get", "<name>", "Retrieve a note.", ".get wifi"),
    ("notes", None, "List notes in this chat.", ".notes"),
    ("rmnote", "<name>", "Delete a note.", ".rmnote wifi"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="utils",
        plugin="notes",
    ).register()
