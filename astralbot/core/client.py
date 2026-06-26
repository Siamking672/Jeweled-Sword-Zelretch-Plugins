"""
Pyrogram client setup and CustomMethods mixin.

Combines the best of both source projects:
- Multi-account assistant support (Zelretch) via DB-stored session strings
- Primary account from STRING_SESSION env var
- Optional assistant bot account via BOT_TOKEN
- CustomMethods mixin with the convenience helpers used across plugins
  (edit, delete, reply, send_document, check_and_log, etc.)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

from pyrogram import Client
from pyrogram.types import Message

if TYPE_CHECKING:
    from astralbot.core.config import Config
    from astralbot.core.database import Database

LOGS = logging.getLogger("astralbot.client")


class CustomMethods:
    """Shared convenience methods mixed into every Pyrogram client.

    Plugins can call ``await client.edit(message, text)``,
    ``await client.delete(message, text)``, etc.
    """

    async def edit(self, message: Message, text: str, **kwargs: Any) -> Message:
        """Edit a message; gracefully create a new one if it can't be edited."""
        try:
            return await message.edit_text(text, **kwargs)
        except Exception:
            return await message.reply_text(text, **kwargs)

    async def delete(self, message: Message, notice: str | None = None, delay: int = 5) -> Message | None:
        """Edit a message to a notice, wait, then delete it. Return the edited msg."""
        if notice:
            try:
                edited = await message.edit_text(notice)
            except Exception:
                edited = await message.reply_text(notice)
            await asyncio.sleep(delay)
            try:
                await edited.delete()
            except Exception:
                pass
            return edited
        try:
            await message.delete()
        except Exception:
            pass
        return None

    async def check_and_log(self, action: str, text: str, count: int = 0) -> None:
        """Send a summary to LOG_CHAT_ID if configured.

        Mirrors Zelretch's check_and_log — useful for broadcast / gcast / mass
        actions where the user wants a follow-up report in their log channel.
        """
        from astralbot import Config, client as _primary
        if not Config or not Config.log_chat_id or not _primary:
            return
        try:
            summary = f"**{action}** | {text}"
            if count:
                summary += f"\nAffected: `{count}`"
            await _primary.send_message(Config.log_chat_id, summary)
        except Exception:
            pass

    async def safe_send(self, chat_id: int | str, text: str, **kwargs: Any) -> Message | None:
        """Best-effort send — never raises."""
        try:
            return await self.send_message(chat_id, text, **kwargs)
        except Exception as exc:
            LOGS.debug("safe_send failed: %s", exc)
            return None

    async def progress_callback(self, current: int, total: int, status_msg: Message | None = None, label: str = "Progress") -> None:
        """Progress callback for downloads / uploads. Throttled to 1 update/sec."""
        if status_msg is None:
            return
        # Throttle to once per second
        now = time.time()
        if not hasattr(status_msg, "_last_progress") or now - status_msg._last_progress > 1:  # type: ignore[attr-defined]
            status_msg._last_progress = now  # type: ignore[attr-defined]
            pct = (current * 100) / total if total else 0
            bar_len = 20
            filled = int(bar_len * current // total) if total else 0
            bar = "█" * filled + "░" * (bar_len - filled)
            try:
                await status_msg.edit_text(
                    f"{label}\n`{bar}` `{pct:.1f}%` ({current}/{total})"
                )
            except Exception:
                pass


class AstralClient(CustomMethods, Client):
    """Pyrogram Client with AstralBot's CustomMethods mixed in."""

    pass


async def build_clients(config: "Config", db: "Database") -> list[Client]:
    """Build the primary client + optional assistant bot + any DB-stored sessions.

    Returns a list of clients. The first element is the "primary" — either the
    userbot account (if STRING_SESSION is set) or the assistant bot (if only
    BOT_TOKEN is set, used in wizard-skipped-session mode).
    """
    clients: list[Client] = []

    # 1. Primary userbot account (if STRING_SESSION is configured)
    if config.string_session:
        primary = AstralClient(
            name="astralbot_primary",
            api_id=config.api_id,
            api_hash=config.api_hash,
            session_string=config.string_session,
            workers=config.workers,
            in_memory=True,
            no_updates=False,
        )
        await primary.start()
        me = await primary.get_me()
        if config.owner_id is None:
            config.owner_id = me.id
            LOGS.info("OWNER_ID auto-detected: %s", config.owner_id)
        LOGS.info("Primary userbot client started: @%s (%s)", me.username, me.id)
        clients.append(primary)
    else:
        LOGS.warning(
            "STRING_SESSION not set — running in assistant-bot-only mode. "
            "Use the `.session` command to create a userbot session later."
        )

    # 2. Optional assistant bot account
    if config.bot_token:
        try:
            bot = AstralClient(
                name="astralbot_assistant_bot",
                api_id=config.api_id,
                api_hash=config.api_hash,
                bot_token=config.bot_token,
                workers=config.workers,
                in_memory=True,
            )
            await bot.start()
            bot_me = await bot.get_me()
            LOGS.info("Assistant bot started: @%s", bot_me.username)
            clients.append(bot)
        except Exception as exc:
            LOGS.warning("Failed to start assistant bot: %s", exc)

    # 3. DB-stored additional sessions (multi-account support, Zelretch-style)
    try:
        sessions = await db.find("sessions")
        for i, sess in enumerate(sessions, start=1):
            try:
                extra = AstralClient(
                    name=f"astralbot_extra_{i}",
                    api_id=config.api_id,
                    api_hash=config.api_hash,
                    session_string=sess["session"],
                    workers=config.workers,
                    in_memory=True,
                )
                await extra.start()
                extra_me = await extra.get_me()
                LOGS.info("Extra client #%d started: @%s", i, extra_me.username)
                clients.append(extra)
            except Exception as exc:
                LOGS.warning("Failed to start extra session #%d: %s", i, exc)
    except Exception as exc:
        LOGS.debug("No extra sessions to load: %s", exc)

    return clients


async def stop_clients(clients: list[Client]) -> None:
    for c in clients:
        try:
            await c.stop()
        except Exception:
            pass
