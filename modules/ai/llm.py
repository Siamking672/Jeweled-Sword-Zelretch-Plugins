"""LLM — chat with an LLM via OpenRouter or direct Gemini API.

API keys are user-provided via .setvar:
    .setvar LLM_PROVIDER openrouter
    .setvar LLM_API_KEY sk-or-v1-...
    .setvar LLM_MODEL anthropic/claude-3.5-sonnet

    .setvar LLM_PROVIDER gemini
    .setvar LLM_API_KEY AIza...
    .setvar LLM_MODEL gemini-1.5-flash

NO bundled API keys — users must provide their own. (See ATTRIBUTION.md for
why we removed the live OpenRouter key shipped in CustomModules/ai.py.)
"""

from __future__ import annotations

import json
from typing import Any

from astralbot import on_command, help_menu, Config, db
from astralbot.helpers.net import post_json, fetch_json


__plugin_name__ = "LLM"
__plugin_author__ = "AstralBot Team"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Chat with an LLM via OpenRouter or Google Gemini."
__plugin_category__ = "ai"


HISTORY_COLLECTION = "llm_history"
MAX_HISTORY = 10  # last N turns kept per user


async def _get_llm_config() -> tuple[str, str, str]:
    provider = await db.get_env("LLM_PROVIDER", default="openrouter")
    api_key = await db.get_env("LLM_API_KEY", default=None)
    model = await db.get_env("LLM_MODEL", default=None)
    if not api_key:
        raise RuntimeError(
            "No LLM_API_KEY set. Use `.setvar LLM_API_KEY <key>` first."
        )
    if provider == "openrouter" and not model:
        model = "openai/gpt-4o-mini"
    elif provider == "gemini" and not model:
        model = "gemini-1.5-flash"
    return provider, api_key, model


async def _call_openrouter(api_key: str, model: str, messages: list[dict], user_id: int) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/AstralBot/AstralBot",
        "X-Title": "AstralBot",
    }
    body = {
        "model": model,
        "messages": messages,
        "max_tokens": 1500,
    }
    result = await post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        body=body,
        headers=headers,
    )
    if not isinstance(result, dict):
        return f"[error] Unexpected response: {result}"
    if "error" in result:
        return f"[error] {result['error']}"
    return result.get("choices", [{}])[0].get("message", {}).get("content", "[no response]")


async def _call_gemini(api_key: str, model: str, messages: list[dict], user_id: int) -> str:
    # Gemini uses a different API shape
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})
    body = {"contents": contents}
    result = await post_json(url, body=body)
    if not isinstance(result, dict):
        return f"[error] Unexpected response: {result}"
    if "error" in result:
        return f"[error] {result['error'].get('message', result['error'])}"
    candidates = result.get("candidates", [])
    if not candidates:
        return "[no response]"
    return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "[no text]")


async def _call_llm(messages: list[dict], user_id: int) -> str:
    provider, api_key, model = await _get_llm_config()
    if provider == "gemini":
        return await _call_gemini(api_key, model, messages, user_id)
    return await _call_openrouter(api_key, model, messages, user_id)


async def _get_history(user_id: int) -> list[dict]:
    doc = await db.get(HISTORY_COLLECTION, {"_id": user_id})
    return doc["messages"] if doc else []


async def _save_history(user_id: int, messages: list[dict]) -> None:
    # Keep only last MAX_HISTORY*2 messages (each turn = user + assistant)
    trimmed = messages[-(MAX_HISTORY * 2):]
    await db.insert(HISTORY_COLLECTION, {
        "_id": user_id,
        "messages": trimmed,
    })


@on_command("ai", description="Chat with an LLM (OpenRouter or Gemini).", permission="sudo")
async def ai_cmd(client, message):
    raw = message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}ai <prompt>`")
    prompt = parts[1]
    user_id = message.from_user.id if message.from_user else 0

    msg = await message.edit_text("🤖 Thinking...")

    try:
        history = await _get_history(user_id)
        history.append({"role": "user", "content": prompt})
        response = await _call_llm(history, user_id)
        history.append({"role": "assistant", "content": response})
        await _save_history(user_id, history)

        # Truncate response for Telegram
        if len(response) > 3500:
            response = response[:3500] + "\n... (truncated)"
        await msg.edit_text(f"🤖 {response}")
    except Exception as exc:
        await msg.edit_text(f"❌ Failed: `{exc}`")


@on_command("aiclear", description="Clear your LLM chat history.", permission="sudo")
async def aiclear_cmd(client, message):
    if not message.from_user:
        return
    await db.delete(HISTORY_COLLECTION, {"_id": message.from_user.id})
    await message.edit_text("🗑️ LLM history cleared.")


@on_command("aiset", description="Configure LLM (provider/key/model).", permission="owner")
async def aiset_cmd(client, message):
    raw = message.text or ""
    parts = raw.split()
    if len(parts) < 3:
        provider = await db.get_env("LLM_PROVIDER", default="openrouter")
        model = await db.get_env("LLM_MODEL", default="(not set)")
        key_set = bool(await db.get_env("LLM_API_KEY", default=None))
        return await message.edit_text(
            f"**LLM config**\n"
            f"  Provider: `{provider}`\n"
            f"  Model: `{model}`\n"
            f"  API key: `{'set' if key_set else 'NOT SET'}`\n"
            f"\n"
            f"Usage:\n"
            f"  `{Config.primary_prefix}aiset provider <openrouter|gemini>`\n"
            f"  `{Config.primary_prefix}aiset key <api-key>`\n"
            f"  `{Config.primary_prefix}aiset model <model-name>`"
        )
    sub = parts[1].lower()
    val = parts[2]
    if sub == "provider":
        if val not in ("openrouter", "gemini"):
            return await message.edit_text("Provider must be openrouter or gemini.")
        await db.set_env("LLM_PROVIDER", val)
        await message.edit_text(f"✅ LLM provider: `{val}`")
    elif sub == "key":
        await db.set_env("LLM_API_KEY", val)
        await message.edit_text("✅ LLM API key saved.")
    elif sub == "model":
        await db.set_env("LLM_MODEL", val)
        await message.edit_text(f"✅ LLM model: `{val}`")
    else:
        await message.edit_text("Unknown subcommand. Use provider / key / model.")


for cmd, args, desc, ex in [
    ("ai", "<prompt>", "Chat with an LLM.", ".ai What is the meaning of life?"),
    ("aiclear", None, "Clear your LLM chat history.", ".aiclear"),
    ("aiset", "provider|key|model <val>", "Configure LLM.", ".aiset provider gemini"),
]:
    help_menu.add(
        command=cmd,
        args=args,
        description=desc,
        example=ex,
        category="ai",
        plugin="llm",
    ).register()
