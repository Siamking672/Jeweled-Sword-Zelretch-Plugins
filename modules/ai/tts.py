"""TTS — text to speech via edge-tts (free, no API key needed)."""

from __future__ import annotations

import asyncio
from io import BytesIO

from astralbot import on_command, help_menu, Config, db


__plugin_name__ = "TTS"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Convert text to speech using edge-tts (free, no API key)."
__plugin_category__ = "ai"


@on_command("tts", description="Convert text to speech.", permission="sudo")
async def tts_cmd(client, message):
    raw = message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}tts <text>`")
    text = parts[1]
    if len(text) > 500:
        return await message.edit_text("Text too long (max 500 chars).")

    voice = await db.get_env("TTS_VOICE", default="en-US-AriaNeural")

    msg = await message.edit_text("🔊 Generating speech...")
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        buf = BytesIO()
        buf.name = "tts.mp3"
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        buf.seek(0)
        await msg.delete()
        await message.reply_voice(buf, caption=f"🔊 `{voice}`: {text[:50]}{'...' if len(text) > 50 else ''}")
    except ImportError:
        await msg.edit_text("❌ `edge-tts` not installed. Run: `pip install edge-tts`")
    except Exception as exc:
        await msg.edit_text(f"❌ Failed: `{exc}`")


@on_command("ttsvoices", description="List available TTS voices (filter by locale).", permission="sudo")
async def ttsvoices_cmd(client, message):
    try:
        import edge_tts
    except ImportError:
        return await message.edit_text("❌ `edge-tts` not installed.")
    locale_filter = message.command[1].lower() if len(message.command) > 1 else None
    msg = await message.edit_text("⏳ Fetching voices...")
    voices = []
    async for v in edge_tts.list_voices():
        if locale_filter and locale_filter not in v["Locale"].lower():
            continue
        voices.append(f"  • `{v['ShortName']}` — {v['FriendlyName']}")
        if len(voices) >= 30:
            break
    if not voices:
        await msg.edit_text("No voices found.")
        return
    text = f"**TTS voices{' (' + locale_filter + ')' if locale_filter else ''}:**\n" + "\n".join(voices)
    await msg.edit_text(text)


for cmd, args, desc, ex in [
    ("tts", "<text>", "Convert text to speech (edge-tts).", ".tts Hello world!"),
    ("ttsvoices", "[locale]", "List available TTS voices.", ".ttsvoices en-us"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="ai",
        plugin="tts",
    ).register()
