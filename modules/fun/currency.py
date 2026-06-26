"""Currency — convert currency via open.er-api.com (no API key)."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config
from astralbot.helpers.net import fetch_json


__plugin_name__ = "Currency"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Convert currency using free open.er-api.com (no API key)."
__plugin_category__ = "fun"


@on_command("currency", description="Convert currency: .currency <amount> <from> <to>.", permission="public")
async def currency_cmd(client, message):
    if len(message.command) < 4:
        return await message.edit_text(
            f"Usage: `{Config.primary_prefix}currency <amount> <from> <to>`\n"
            f"Example: `.currency 100 USD EUR`"
        )
    try:
        amount = float(message.command[1])
    except ValueError:
        return await message.edit_text("Amount must be a number.")
    src = message.command[2].upper()
    dst = message.command[3].upper()

    msg = await message.edit_text(f"💱 Converting `{amount} {src}` → `{dst}`...")
    try:
        data = await fetch_json(f"https://open.er-api.com/v6/latest/{src}")
        if not isinstance(data, dict) or data.get("result") != "success":
            return await msg.edit_text(f"❌ API error: {data}")
        rate = data.get("rates", {}).get(dst)
        if not rate:
            return await msg.edit_text(f"❌ No rate for `{dst}`.")
        converted = amount * rate
        await msg.edit_text(
            f"💱 **Currency conversion**\n"
            f"  `{amount} {src}` = `{converted:.2f} {dst}`\n"
            f"  Rate: `1 {src} = {rate:.4f} {dst}`\n"
            f"  Updated: `{data.get('time_last_update_utc', '?')}`"
        )
    except Exception as exc:
        await msg.edit_text(f"❌ Failed: `{exc}`")


help_menu.add(
    command="currency",
    args="<amount> <from> <to>",
    description="Convert currency (free API).",
    example=".currency 100 USD EUR",
    category="fun",
    plugin="currency",
).register()
