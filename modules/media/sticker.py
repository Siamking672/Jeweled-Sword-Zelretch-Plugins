"""Sticker — kang stickers, get sticker info."""

from __future__ import annotations

import asyncio
import os
from io import BytesIO
from pathlib import Path

from astralbot import on_command, help_menu, Config, db


__plugin_name__ = "Sticker"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Kang stickers, get sticker pack info, manage sticker packs."
__plugin_category__ = "media"


@on_command("kang", description="Kang a sticker or image to your pack.", permission="sudo")
async def kang_cmd(client, message):
    target = message.reply_to_message
    if not target or not (target.sticker or target.photo or target.document):
        return await message.edit_text("Reply to a sticker or image to kang it.")

    # Get pack name from env or use default
    pack_name = await db.get_env("STICKER_PACKNAME", default=f"a_{message.from_user.id}_by_astralbot")
    pack_title = await db.get_env("STICKER_PACKTITLE", default="My AstralBot Stickers")

    msg = await message.edit_text("🐾 Kanging...")

    try:
        # Download the source media
        path = await client.download_media(target, in_memory=True)
        if not path:
            return await msg.edit_text("❌ Failed to download source media.")

        # If it's already a sticker, just re-upload; if it's a photo, resize via Pillow
        if target.sticker:
            sticker_bytes = path
        else:
            # Convert image to PNG and resize to 512x512 (one side)
            try:
                from PIL import Image
                img = Image.open(path).convert("RGBA")
                # Resize so longest side is 512
                w, h = img.size
                if w > h:
                    new_w, new_h = 512, int(h * 512 / w)
                else:
                    new_w, new_h = int(w * 512 / h), 512
                img = img.resize((new_w, new_h), Image.LANCZOS)
                buf = BytesIO()
                buf.name = "sticker.png"
                img.save(buf, format="PNG")
                buf.seek(0)
                sticker_bytes = buf
            except ImportError:
                return await msg.edit_text("❌ Pillow not installed — required for image conversion.")

        # Add to sticker pack
        try:
            await client.add_sticker_to_set(
                name=pack_name,
                user_id=message.from_user.id,
                sticker=sticker_bytes,
                emojis=target.sticker.emoji if target.sticker else "🐾",
            )
            action = "Added to existing pack"
        except Exception:
            # Pack doesn't exist — create it
            await client.create_new_sticker_set(
                user_id=message.from_user.id,
                title=str(pack_title),
                name=pack_name,
                stickers=[{
                    "sticker": sticker_bytes,
                    "emoji": target.sticker.emoji if target.sticker else "🐾",
                }],
            )
            action = "Created new pack"

        await msg.edit_text(
            f"✅ {action}\n"
            f"Pack: [{pack_title}](https://t.me/addstickers/{pack_name})"
        )
    except Exception as exc:
        await msg.edit_text(f"❌ Failed: `{exc}`")


@on_command("stickerinfo", description="Get info about a replied sticker.", permission="public")
async def stickerinfo_cmd(client, message):
    target = message.reply_to_message
    if not target or not target.sticker:
        return await message.edit_text("Reply to a sticker.")
    s = target.sticker
    text = (
        f"**Sticker info**\n"
        f"  Set name: `{s.set_name or 'n/a'}`\n"
        f"  File ID: `{s.file_id}`\n"
        f"  Size: `{s.width}x{s.height}`\n"
        f"  File size: `{s.file_size or '?'} bytes`\n"
        f"  Emoji: `{s.emoji or 'n/a'}`\n"
        f"  Animated: `{s.is_animated}`\n"
        f"  Video: `{s.is_video}`"
    )
    await message.edit_text(text)


for cmd, args, desc, ex in [
    ("kang", "<reply>", "Kang a sticker or image to your pack.", ".kang (reply)"),
    ("stickerinfo", "<reply>", "Get info about a sticker.", ".stickerinfo (reply)"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="media",
        plugin="sticker",
    ).register()
