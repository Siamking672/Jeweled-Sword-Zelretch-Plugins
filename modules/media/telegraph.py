"""Telegraph — create Telegraph pages from replied text."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config
from astralbot.helpers.net import post_json


__plugin_name__ = "Telegraph"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Create telegra.ph pages from replied text messages."
__plugin_category__ = "media"


@on_command("telegraph", description="Create a Telegraph page from replied text.", permission="sudo")
async def telegraph_cmd(client, message):
    target = message.reply_to_message
    if not target or not (target.text or target.caption):
        return await message.edit_text("Reply to a text message to create a Telegraph page.")
    content = target.text or target.caption
    msg = await message.edit_text("📡 Creating Telegraph page...")

    # Build minimal Telegraph content
    title = content.split("\n")[0][:80] or "Telegraph Page"
    body = "".join(f"<p>{line}</p>" for line in content.split("\n") if line.strip())

    try:
        result = await post_json(
            "https://api.telegra.ph/createPage",
            {
                "access_token": "anon",  # anonymous — Telegraph lets anyone post
                "title": title,
                "author_name": "AstralBot",
                "content": body,
                "return_content": False,
            },
        )
        if not isinstance(result, dict) or not result.get("ok"):
            return await msg.edit_text(f"❌ Telegraph API error: {result}")
        url = result["result"]["url"]
        await msg.edit_text(f"📡 Telegraph page created:\n{url}")
    except Exception as exc:
        await msg.edit_text(f"❌ Failed: `{exc}`")


help_menu.add(
    command="telegraph",
    args="<reply>",
    description="Create a Telegraph page from a replied text message.",
    example=".telegraph (reply)",
    category="media",
    plugin="telegraph",
).register()
