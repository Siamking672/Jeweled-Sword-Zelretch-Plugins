# Attribution & Credits — AstralModules

This plugin repository is part of AstralBot and is licensed under the same
**GNU General Public License v3.0** as the main project. See [LICENSE](LICENSE).

## Source projects

### Zelretch-Plugins (https://github.com/Siamking672/Zelretch-Plugins)

- **License:** GNU GPL v3.0
- **Author:** Siamking672
- **Original lineage:** Zelretch-Plugins is itself a retheme of the Hellbot
  userbot. The architectural patterns (HelpMenu fluent builder, ENV class,
  tiered permissions, multi-account support) come from Hellbot via Zelretch.
- **What we reused (concepts, not verbatim code):**
  - Plugin organization by category (`admin/`, `utils/`, `media/`, etc.)
  - The `HelpMenu` fluent builder API
  - The `@on_message` decorator pattern (re-implemented as `@on_command`)
  - The `allow_master=True` sudo flag (re-implemented as `allow_sudo=True`)
  - The DB-backed runtime config pattern (`get_env` / `set_env`)
  - Plugin categories: admin (admins, purge, lock, federation), utils
    (afk, notes, filters, warns, greetings, snips, antiflood), media
    (download, upload, sticker, songs, telegraph), privacy (pmpermit,
    blacklist, antipin)
- **What we did NOT carry over:**
  - The Rin Tohsaka / Fate theme (all `zelretch_*` and `hellbot_*` image
    assets were dropped).
  - The hardcoded dev user IDs (`Config.DEVS = filters.user([...])`).
  - The Kurigram drop-in package — we use stock Pyrogram v2.
  - The MongoDB-only database layer — we use SQLite default + Mongo optional.
  - The `"𝐇𝐞𝐥𝐥𝐁𝐨𝐭 𝐏𝐌 𝐒𝐞𝐜𝐮𝐫𝐢𝐭𝐲!"` user-facing string — replaced with
    a configurable `PM_TEMPLATE` runtime env var.
  - The `@ForGo10God` examples in help text.

### FoxUserbot CustomModules (https://github.com/FoxUserbot/CustomModules)

- **License:** No top-level LICENSE file. Individual files claim AGPL-3.0
  (we respect those claims).
- **Authors (per-file):**
  - @codrago_m / @codrago — `PromoClaimer.py` (AGPL-3.0)
  - qq_shark — `media2gif.py` (AGPL-3.0)
  - xdesai (mods.xdesai.top) — `weather_xdesai.py`, `currency.py`, `url.py`,
    `ipinfo.py`, `ToDo.py`, `stats_xdesai.py`
  - KOTmodules — `KOTaiwaifu.py`
  - AmokDEV — `hearts.py` (refactored by A9FM)
- **What we reused (concepts, not verbatim code):**
  - The trilingual `LANGUAGES` dict + `get_text()` i18n pattern (preserved
    in `modules/_i18n.py`)
  - The `fox_command() + fox_sudo()` decorator idiom (re-implemented as
    `@on_command(..., allow_sudo=True)`)
  - Module concepts: weather (wttr.in instead of OpenWeatherMap to avoid
    the bundled API key), currency (open.er-api.com), wikipedia, QR code,
    whois, animate (hearts, ladder, progressbar — rewritten to fix the
    infinite-loop and bare-except bugs in the source)
- **What we did NOT carry over:**
  - **No bundled API keys.** The OpenRouter key in `ai.py` and
    `wine_hikka.py`, the Last.fm key in `lastfm.py`, the OpenWeatherMap key
    in `weather_xdesai.py`, the Genius key in `find_music.py`, the rule34
    account creds in `rule34.py`, and the OK.ru CALLS_API_KEY in
    `telega_detector.py` were ALL dropped. Users provide their own keys via
    `.setvar` or env vars.
  - **No legally/ethically risky modules.** We did not port:
    - `Bull.py` / `AuroraBull.py` (obscene harassment generators)
    - `патриот.py` (political Z-symbol generator)
    - `HistoryFacts.py` (politically sensitive WWII "facts")
    - `db0mb3r.py` (SMS bomber, illegal in many jurisdictions)
    - `rule34.py` (NSFW)
    - `wine_hikka.py` (depended on the bundled OpenRouter key)
  - **No broken modules.** We did not port modules with known bugs in
    the source (the `lastfm.py` import-time threading.Thread, the
    `autoonline.py` infinite `while True` loop, the `KOTaiwaifu.py`
    binary-as-text write, the `quotes.py` infinite loop on non-sticker
    response, etc.).
  - The custom `who_message()` shim (FoxUserbot'sudo-user-in-groups hack)
    was not needed — our `@on_command` decorator handles sudo enforcement
    directly via `filters.me | filters.user(sudo_list)`.

## License of AstralModules

GNU General Public License v3.0. See [LICENSE](LICENSE).

## Contributors

- AstralBot Team — refined fork-style rebuild combining Zelretch and
  FoxUserbot design ideas.

If you contribute, please add yourself here in your first PR.
