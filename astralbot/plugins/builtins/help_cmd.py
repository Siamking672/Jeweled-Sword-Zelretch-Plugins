"""Help builtin — renders the command index."""

from __future__ import annotations

from astralbot import on_command, help_menu, Config

__plugin_name__ = "Help"
__plugin_author__ = "AstralBot"
__plugin_version__ = "1.0.0"
__plugin_license__ = "GPL-3.0"
__plugin_description__ = "Show available commands and plugin info."
__plugin_category__ = "core"


@on_command(["help", "h"], description="Show all available commands.", permission="sudo")
async def help_cmd(client, message):
    prefix = Config.primary_prefix if Config else "."
    text = help_menu.render_help(prefix=prefix)
    if len(text) > 4096:
        from astralbot.helpers.paste import paste
        url = await paste(text)
        await message.edit_text(
            f"📋 Too many commands for one message.\nFull help: {url}"
        )
        return
    await message.edit_text(text)


@on_command("plinfo", description="List loaded plugins with metadata.", permission="sudo")
async def plinfo_cmd(client, message):
    text = help_menu.render_plugin_list()
    await message.edit_text(text)


@on_command("cmdinfo", description="Show details for a single command.", permission="sudo")
async def cmdinfo_cmd(client, message):
    if len(message.command) < 2:
        return await message.edit_text(f"Usage: `{Config.primary_prefix}cmdinfo <command>`")
    name = message.command[1].lstrip(Config.primary_prefix)
    cmd = help_menu.all_commands().get(name)
    if not cmd:
        return await message.edit_text(f"Command `{name}` not found.")
    text = (
        f"**Command:** `{Config.primary_prefix}{cmd.command}`\n"
        f"**Plugin:** `{cmd.plugin}`\n"
        f"**Category:** `{cmd.category}`\n"
        f"**Description:** {cmd.description}\n"
    )
    if cmd.args:
        text += f"**Args:** `{cmd.args}`\n"
    if cmd.example:
        text += f"**Example:** `{Config.primary_prefix}{cmd.example}`\n"
    if cmd.aliases:
        text += f"**Aliases:** {', '.join('`' + a + '`' for a in cmd.aliases)}\n"
    if cmd.note:
        text += f"**Note:** {cmd.note}\n"
    await message.edit_text(text)
