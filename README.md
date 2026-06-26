# 📦 AstralModules

> Official plugin repository for [AstralBot](https://github.com/AstralBot/AstralBot).

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![AstralBot](https://img.shields.io/badge/AstralBot-v1.0.0-orange.svg)](https://github.com/AstralBot/AstralBot)

---

## Table of Contents

- [Overview](#overview)
- [Plugin categories](#plugin-categories)
- [Installation](#installation)
  - [Automatic (recommended)](#automatic-recommended)
  - [Manual](#manual)
  - [Single-plugin install](#single-plugin-install)
- [Plugin contract](#plugin-contract)
- [Writing your own plugin](#writing-your-own-plugin)
- [i18n](#i18n)
- [Configuration](#configuration)
- [Credits & license](#credits--license)

---

## Overview

This repository contains the official set of plugins loaded by AstralBot at
startup. Each plugin is a single Python file organised by category, with
declarative manifest metadata (`__plugin_name__`, `__plugin_version__`, etc.)
and commands registered via AstralBot's `@on_command` decorator.

The plugin repo is **completely separate** from the main project — the main
project downloads this repo as a zip at startup (or on `.update`) and loads
it from `userdata/external_plugins/modules/`.

## Plugin categories

| Category | Plugins | Description |
|---|---|---|
| `admin/` | `admins`, `purge`, `lock` | Group administration: promote, demote, ban, kick, mute, pin, purge, lock |
| `utils/` | `afk`, `notes`, `warns`, `snips`, `greetings`, `antiflood` | Utilities: AFK auto-reply, notes, warns, snips, welcome/goodbye, antiflood |
| `media/` | `download`, `qr`, `telegraph`, `sticker` | Media tools: download, QR codes, Telegraph pages, sticker kanging |
| `ai/` | `llm`, `tts` | AI: LLM chat (OpenRouter/Gemini), text-to-speech (edge-tts) |
| `fun/` | `weather`, `currency`, `wikipedia`, `whois`, `animate` | Fun & info: weather, currency, Wikipedia, whois, animated text |
| `privacy/` | `pmpermit`, `blacklist`, `antipin`, `antichannel` | Privacy: PM permit, word blacklist, antipin, antichannel |

A full command reference is available in-bot via `.help` (categorised) or
`.cmdinfo <command>` (single-command details).

## Installation

### Automatic (recommended)

If you're running AstralBot with the default `PLUGIN_REPO=AstralBot/AstralModules`
env var, **this repository is pulled automatically at startup** and on every
`.update` command. You don't need to do anything.

To verify:

```
.list
```

You should see all the plugins listed with ✅ status.

### Manual

If you want to manage plugins yourself (e.g. fork this repo and customise):

1. Fork this repo to your own GitHub account.
2. In your AstralBot `.env`:

   ```env
   PLUGIN_REPO=YourUsername/YourModules
   PLUGIN_BRANCH=main
   PLUGIN_PATH=modules
   ```

3. Restart AstralBot (or run `.update`).

### Single-plugin install

To install a single plugin (e.g. one you found in another repo or wrote
yourself):

1. Send the `.py` file as a document to any chat where AstralBot is running.
2. Reply to it with:

   ```
   .install myplugin
   ```

The plugin is saved to `userdata/plugins/myplugin.py` and loaded immediately.

To uninstall:

```
.uninstall myplugin
```

## Plugin contract

Each plugin is a single `.py` file. It MAY declare module-level manifest
attributes (recommended):

```python
__plugin_name__        = "Admin Tools"
__plugin_author__      = "Your Name"
__plugin_version__     = "1.0.0"
__plugin_license__     = "GPL-3.0"
__plugin_description__ = "Group administration commands."
__plugin_category__    = "admin"               # admin|utils|media|ai|fun|privacy|misc
__plugin_deps__        = []                    # optional pip deps (informational)
__plugin_min_core__    = "1.0.0"               # minimum AstralBot version
```

Commands are registered via `@on_command`:

```python
from astralbot import on_command, help_menu, Config

@on_command("hello", description="Say hello.", permission="sudo")
async def hello_cmd(client, message):
    await message.edit_text("Hello, world!")

help_menu.add(
    command="hello",
    description="Say hello.",
    example=".hello",
    category="fun",
    plugin="hello",
).register()
```

For non-command watchers (AFK auto-reply, antiflood, pmpermit):

```python
from astralbot import on_event
from pyrogram import filters

@on_event(filters.incoming & filters.private)
async def my_watcher(client, message):
    ...
```

See the [main project README](https://github.com/AstralBot/AstralBot#plugin-system)
for the full API reference.

## Writing your own plugin

Minimal example — save as `userdata/plugins/hello.py`:

```python
from astralbot import on_command, help_menu

__plugin_name__ = "Hello"
__plugin_author__ = "Me"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "A minimal hello-world plugin."
__plugin_category__ = "fun"


@on_command("hello", description="Say hello.", permission="public")
async def hello_cmd(client, message):
    name = message.from_user.first_name if message.from_user else "stranger"
    await message.edit_text(f"👋 Hello, {name}!")


help_menu.add(
    command="hello",
    description="Say hello to the user.",
    example=".hello",
    category="fun",
    plugin="hello",
).register()
```

Then:

```
.load hello
.hello
```

## i18n

AstralModules ships a trilingual (en/ru/ua) i18n pattern based on FoxUserbot's
`LANGUAGES` dict convention. Any plugin can declare a `LANGUAGES` dict and
use `get_text()`:

```python
from modules._i18n import get_text

LANGUAGES = {
    "en": {"hello": "Hello, {name}!"},
    "ru": {"hello": "Привет, {name}!"},
    "ua": {"hello": "Привіт, {name}!"},
}

@on_command("hello", description="Localized hello.", permission="public")
async def hello_cmd(client, message):
    name = message.from_user.first_name if message.from_user else "stranger"
    text = await get_text("hello_plugin", "hello", LANGUAGES=LANGUAGES, name=name)
    await message.edit_text(text)
```

The current language is read from the DB via `db.get_env("LANG")` (default:
`en`). Users can change it with:

```
.setvar LANG ru
```

## Configuration

Most plugin config is stored in the AstralBot DB via `db.get_env` /
`db.set_env`. See [the main project README](https://github.com/AstralBot/AstralBot#configuration)
for details.

Plugin-specific env vars used by AstralModules:

| Var | Default | Plugin | Description |
|---|---|---|---|
| `LANG` | `en` | (all) | UI language (en/ru/ua) |
| `WARN_LIMIT` | `3` | warns | Auto-ban threshold |
| `PM_MAX_SPAM` | `3` | pmpermit | Auto-block threshold |
| `PM_TEMPLATE` | (see code) | pmpermit | Warning message template (`{count}` and `{max}` placeholders) |
| `STICKER_PACKNAME` | `a_<uid>_by_astralbot` | sticker | Your sticker pack name |
| `STICKER_PACKTITLE` | `My AstralBot Stickers` | sticker | Display title |
| `TTS_VOICE` | `en-US-AriaNeural` | tts | edge-tts voice name |
| `LLM_PROVIDER` | `openrouter` | llm | `openrouter` or `gemini` |
| `LLM_API_KEY` | (none) | llm | Your API key |
| `LLM_MODEL` | `openai/gpt-4o-mini` | llm | Model name |

Set any of these with `.setvar <KEY> <VALUE>` from Telegram.

## Credits & license

AstralModules is licensed under the **GNU General Public License v3.0** — the
same license as the source projects it derives from. See [LICENSE](LICENSE)
and [ATTRIBUTION.md](ATTRIBUTION.md) for full credits to:

- **Siamking672** — Zelretch and Zelretch-Plugins (which itself derives from
  the Hellbot userbot)
- **A9FM** (https://t.me/a9_fm) — FoxUserbot
- **ArThirtyFour** (https://t.me/ArThirtyFour) — FoxUserbot
- **Nw_Off** (https://t.me/nw_off) — FoxUserbot design
- Various CustomModules contributors (per-file attribution in ATTRIBUTION.md)

### Differences from the source plugin repos

1. **Manifest-driven.** Every plugin declares `__plugin_name__`,
   `__version__`, `__author__`, `__license__`, `__category__`. Neither
   source repo had this.
2. **No bundled API keys.** All API keys are user-provided via `.setvar`.
   CustomModules shipped live OpenRouter / Last.fm / Genius / rule34 / OK.ru
   keys in public source — we refused to carry these over.
3. **No legally/ethically risky modules.** We did not port the SMS bomber,
   political Z-symbol generator, WWII "facts" generator, obscene
   trash-talk generators, or NSFW rule34 module.
4. **No broken modules.** We rewrote modules that had known bugs in the
   source (the `lastfm.py` import-time threading.Thread, the
   `autoonline.py` infinite `while True` loop, the `KOTaiwaifu.py`
   binary-as-text write, the `quotes.py` infinite loop on non-sticker
   response).
5. **Unified plugin format.** Both source repos had inconsistent plugin
   formats (some with i18n, some without; some with manifests, some
   without; config persisted in different places). AstralModules
   standardises on: manifest at top, `@on_command` for commands, `@on_event`
   for watchers, `db.get_env`/`db.set_env` for config, `modules/_i18n.py`
   for i18n.

---

<p align="center">
  Part of the <a href="https://github.com/AstralBot/AstralBot">AstralBot</a> project.<br>
  Star ⭐ the main repo if you find it useful.
</p>
