"""Wikipedia — fetch article summaries via the official Wikipedia API."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config
from astralbot.helpers.net import fetch_json


__plugin_name__ = "Wikipedia"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Fetch Wikipedia article summaries."
__plugin_category__ = "fun"


@on_command("wiki", description="Get a Wikipedia summary.", permission="public")
async def wiki_cmd(client, message):
    raw = message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}wiki <query>`")
    query = parts[1]
    msg = await message.edit_text(f"📚 Looking up `{query}`...")
    try:
        # Use the REST summary endpoint
        data = await fetch_json(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{query.replace(' ', '_')}"
        )
        if not isinstance(data, dict) or data.get("type") == "https://mediawiki.org/wiki/HyperSwitch/errors/not_found":
            return await msg.edit_text(f"❌ No Wikipedia article found for `{query}`.")
        title = data.get("title", query)
        extract = data.get("extract", "(no extract)")
        url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
        text = f"📚 **{title}**\n\n{extract}"
        if url:
            text += f"\n\n[Read more]({url})"
        if len(text) > 4000:
            text = text[:4000] + "..."
        await msg.edit_text(text)
    except Exception as exc:
        await msg.edit_text(f"❌ Failed: `{exc}`")


help_menu.add(
    command="wiki",
    args="<query>",
    description="Get a Wikipedia summary.",
    example=".wiki Albert Einstein",
    category="fun",
    plugin="wikipedia",
).register()
