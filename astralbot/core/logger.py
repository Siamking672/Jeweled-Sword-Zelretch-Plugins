"""
Logging setup.

Combines best practices from both source projects:
- Rotating file handler (Zelretch style: 5 MB x 10 backups)
- Console handler with colour-free format
- Optional Telegram log channel handler (NEW — neither source had this)
  that forwards WARNING+ to LOG_CHAT_ID for hosted deployments where SSH
  access is unavailable (FoxUserbot had no error reporter at all).
"""

from __future__ import annotations

import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


class TelegramLogHandler(logging.Handler):
    """Forward WARNING+ log records to a Telegram chat (async, non-blocking)."""

    def __init__(self, client, chat_id: int, level=logging.WARNING):
        super().__init__(level)
        self._client = client
        self._chat_id = chat_id
        self._queue: asyncio.Queue[logging.LogRecord] = asyncio.Queue(maxsize=200)
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._pump())

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._queue.put_nowait(record)
        except asyncio.QueueFull:
            # Drop oldest to make room — never block logging
            try:
                self._queue.get_nowait()
                self._queue.put_nowait(record)
            except Exception:
                pass

    async def _pump(self) -> None:
        while True:
            record = await self._queue.get()
            try:
                text = self.format(record)
                if len(text) > 3900:
                    text = text[:3900] + "\n... (truncated)"
                await self._client.send_message(self._chat_id, f"```\n{text}\n```")
            except Exception:
                # Never let a logging failure crash the bot
                pass


def setup_logging(log_path: Path | str = "astralbot.log", telegram_client=None, log_chat_id: int | None = None) -> logging.Logger:
    """Configure root logger with file + console, and optional Telegram sink."""
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    # Wipe any pre-existing handlers (prevents duplicate output across reloads)
    for h in list(root.handlers):
        root.removeHandler(h)

    root.setLevel(logging.INFO)

    file_h = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8",
    )
    file_h.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(file_h)

    console_h = logging.StreamHandler(sys.stdout)
    console_h.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root.addHandler(console_h)

    # Suppress noisy third-party loggers
    for noisy in ("pyrogram", "kurigram", "urllib3", "asyncio", "motor"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    if telegram_client is not None and log_chat_id:
        tg_h = TelegramLogHandler(telegram_client, log_chat_id, level=logging.WARNING)
        tg_h.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        tg_h.start()
        root.addHandler(tg_h)

    logs = logging.getLogger("astralbot")
    logs.info("Logging initialised → file=%s, telegram=%s", log_path, bool(log_chat_id))
    return logs
