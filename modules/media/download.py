"""Download — download media from a replied message or URL."""

from __future__ import annotations

import os
from pathlib import Path

from astralbot import on_command, help_menu, Config, LOGS
from astralbot.helpers.media import download_media, upload_file, human_size


__plugin_name__ = "Download"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Download media from replied messages or URLs."
__plugin_category__ = "media"


@on_command("download", description="Download media from a replied message.", permission="sudo")
async def download_cmd(client, message):
    target = message.reply_to_message
    if not target or not (target.media or target.document or target.video or target.audio or target.photo):
        return await message.edit_text("Reply to a message with media to download.")
    msg = await message.edit_text("⬇️ Downloading...")
    path = await download_media(client, target, dest_dir=Config.data_dir / "downloads")
    if not path:
        return await msg.edit_text("❌ Download failed.")
    size = os.path.getsize(path) if path.exists() else 0
    await msg.edit_text(
        f"✅ Downloaded: `{path.name}`\nSize: `{human_size(size)}`\nPath: `{path}`"
    )


@on_command("upload", description="Upload a file from the server (path arg).", permission="owner")
async def upload_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}upload <server-path>`")
    raw = message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2:
        return await message.edit_text("No path provided.")
    path = Path(parts[1].strip())
    if not path.exists():
        return await message.edit_text(f"❌ File not found: `{path}`")
    msg = await message.edit_text(f"⬆️ Uploading `{path.name}`...")
    sent = await upload_file(client, message.chat.id, path)
    if sent:
        await msg.delete()
    else:
        await msg.edit_text("❌ Upload failed.")


for cmd, args, desc, ex in [
    ("download", "<reply>", "Download media from a replied message.", ".download (reply)"),
    ("upload", "<server-path>", "Upload a file from the server (owner only).", ".upload /etc/hostname"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="media",
        plugin="download",
    ).register()
