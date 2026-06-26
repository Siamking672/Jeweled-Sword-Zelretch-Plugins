"""Animate — fun animated text effects (hearts, ladder, progressbar).

Inspired by CustomModules/hearts.py, ladder.py, progressbar.py — but rewritten
to avoid the bare-except and infinite-loop bugs in those source files.
"""

from __future__ import annotations

import asyncio

from astralbot import on_command, help_menu, Config


__plugin_name__ = "Animate"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Animated text effects: hearts, ladder, progress bar."
__plugin_category__ = "fun"


@on_command("hearts", description="Send an animated hearts message.", permission="sudo")
async def hearts_cmd(client, message):
    raw = message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}hearts <text>`")
    text = parts[1]
    frames = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎"]
    msg = await message.edit_text(f"{frames[0]} {text}")
    for i in range(1, len(frames) * 2):
        emoji = frames[i % len(frames)]
        try:
            await msg.edit_text(f"{emoji} {text}")
        except Exception:
            pass
        await asyncio.sleep(0.5)


@on_command("ladder", description="Send an animated text ladder.", permission="sudo")
async def ladder_cmd(client, message):
    raw = message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}ladder <text>`")
    text = parts[1]
    msg = await message.edit_text("```" + text + "```")
    for i in range(1, min(len(text), 20)):
        try:
            await msg.edit_text("```\n" + " " * i + text + "\n```")
        except Exception:
            pass
        await asyncio.sleep(0.4)


@on_command("progressbar", description="Animated progress bar demo.", permission="sudo")
async def progressbar_cmd(client, message):
    msg = await message.edit_text("`[░░░░░░░░░░░░░░░░░░░░] 0%`")
    total = 20
    for i in range(1, total + 1):
        bar = "█" * i + "░" * (total - i)
        pct = (i / total) * 100
        try:
            await msg.edit_text(f"`[{bar}] {pct:.0f}%`")
        except Exception:
            pass
        await asyncio.sleep(0.3)


for cmd, args, desc, ex in [
    ("hearts", "<text>", "Animated hearts.", ".hearts I love you!"),
    ("ladder", "<text>", "Animated ladder.", ".ladder hello"),
    ("progressbar", None, "Animated progress bar demo.", ".progressbar"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="fun",
        plugin="animate",
    ).register()
