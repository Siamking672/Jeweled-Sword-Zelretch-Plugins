"""QR code generator — encode text as a QR code image."""

from __future__ import annotations

import asyncio
from io import BytesIO

from astralbot import on_command, help_menu, Config
from astralbot.helpers.net import fetch_bytes


__plugin_name__ = "QR Code"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Generate a QR code from text. Uses the public api.qrserver.com service."
__plugin_category__ = "media"


@on_command("qr", description="Generate a QR code from text.", permission="sudo")
async def qr_cmd(client, message):
    raw = message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}qr <text or URL>`")
    text = parts[1]
    msg = await message.edit_text("🔲 Generating QR...")
    try:
        # Try local qrcode library first
        try:
            import qrcode
            img = qrcode.make(text)
            buf = BytesIO()
            buf.name = "qr.png"
            img.save(buf, format="PNG")
            buf.seek(0)
            await msg.delete()
            await message.reply_photo(buf, caption=f"🔲 QR for: `{text[:50]}{'...' if len(text) > 50 else ''}`")
            return
        except ImportError:
            pass

        # Fall back to public API
        url = f"https://api.qrserver.com/v1/create-qr-code/?size=512x512&data={text}"
        data = await fetch_bytes(url)
        if not data:
            return await msg.edit_text("❌ QR generation failed.")
        buf = BytesIO(data)
        buf.name = "qr.png"
        await msg.delete()
        await message.reply_photo(buf, caption=f"🔲 QR for: `{text[:50]}{'...' if len(text) > 50 else ''}`")
    except Exception as exc:
        await msg.edit_text(f"❌ Failed: `{exc}`")


help_menu.add(
    command="qr",
    args="<text|url>",
    description="Generate a QR code from text or a URL.",
    example=".qr https://example.com",
    category="media",
    plugin="qr",
).register()
