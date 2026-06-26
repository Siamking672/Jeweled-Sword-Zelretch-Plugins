"""Weather — current weather via wttr.in (no API key needed)."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config
from astralbot.helpers.net import fetch_text, fetch_json


__plugin_name__ = "Weather"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Current weather via wttr.in (no API key needed)."
__plugin_category__ = "fun"


@on_command("weather", description="Get current weather for a city.", permission="public")
async def weather_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}weather <city>`")
    city = " ".join(message.command[1:])
    msg = await message.edit_text(f"🌤️ Fetching weather for `{city}`...")
    try:
        # wttr.in returns JSON when you append ?format=j1
        data = await fetch_json(f"https://wttr.in/{city}?format=j1")
        if not isinstance(data, dict) or "current_condition" not in data:
            return await msg.edit_text(f"❌ Could not fetch weather for `{city}`.")
        cur = data["current_condition"][0]
        area = data.get("nearest_area", [{}])[0]
        location = f"{area.get('areaName', [{}])[0].get('value', city)}, {area.get('country', [{}])[0].get('value', '')}"
        text = (
            f"🌤️ **Weather: {location}**\n"
            f"\n"
            f"  Temperature: `{cur['temp_C']}°C` (feels like `{cur['FeelsLikeC']}°C`)\n"
            f"  Condition: {cur['weatherDesc'][0]['value']}\n"
            f"  Humidity: `{cur['humidity']}%`\n"
            f"  Wind: `{cur['windspeedKmph']} km/h` ({cur['winddir16Point']})\n"
            f"  Visibility: `{cur['visibility']} km`\n"
            f"  Pressure: `{cur['pressure']} hPa`\n"
            f"  UV Index: `{cur['uvIndex']}`"
        )
        await msg.edit_text(text)
    except Exception as exc:
        await msg.edit_text(f"❌ Failed: `{exc}`")


help_menu.add(
    command="weather",
    args="<city>",
    description="Get current weather (wttr.in).",
    example=".weather Dhaka",
    category="fun",
    plugin="weather",
).register()
