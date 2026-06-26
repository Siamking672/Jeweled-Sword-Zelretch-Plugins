import asyncio
import glob
import importlib
import os
import sys
from pathlib import Path

import pyroaddon  # pylint: disable=unused-import
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from .config import ENV, Config, Symbols
from .database import db
from .logger import LOGS


class ZelretchClient(Client):
    def __init__(self) -> None:
        self.users: list[Client] = []
        self.bot: Client = Client(
            name="JeweledSwordZelretchBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins=dict(root="zelretch.plugins.bot"),
        )

    async def start_user(self) -> None:
        sessions = await db.get_all_sessions()
        for i, session in enumerate(sessions):
            try:
                client = Client(
                    name=f"ZelretchUser#{i + 1}",
                    api_id=Config.API_ID,
                    api_hash=Config.API_HASH,
                    session_string=session["session"],
                )
                await client.start()
                me = await client.get_me()
                self.users.append(client)
                LOGS.info(
                    f"{Symbols.arrow_right * 2} Started User {i + 1}: '{me.first_name}' {Symbols.arrow_left * 2}"
                )
                is_in_logger = await self.validate_logger(client)
                if not is_in_logger:
                    LOGS.warning(
                        f"Client #{i+1}: '{me.first_name}' is not in Logger Group! Check and add manually for proper functioning."
                    )
                # Do not auto-join any hardcoded promotion/channel chats.
                # User clients should only join chats that are required for bot operation,
                # such as the configured LOGGER_ID handled by validate_logger().
            except Exception as e:
                LOGS.error(f"{i + 1}: {e}")
                continue

    async def start_bot(self) -> None:
        await self.bot.start()
        me = await self.bot.get_me()
        LOGS.info(
            f"{Symbols.arrow_right * 2} Started Jeweled Sword Zelretch Client: '{me.username}' {Symbols.arrow_left * 2}"
        )

    async def load_plugin(self) -> None:
        count = 0
        files = glob.glob("zelretch/plugins/user/*.py")
        unload = await db.get_env(ENV.unload_plugins) or ""
        unload = unload.split(" ")
        for file in files:
            with open(file) as f:
                path = Path(f.name)
                shortname = path.stem.replace(".py", "")
                if shortname in unload:
                    os.remove(Path(f"zelretch/plugins/user/{shortname}.py"))
                    continue
                if shortname.startswith("__"):
                    continue
                fpath = Path(f"zelretch/plugins/user/{shortname}.py")
                name = "zelretch.plugins.user." + shortname
                spec = importlib.util.spec_from_file_location(name, fpath)
                load = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(load)
                sys.modules["zelretch.plugins.user." + shortname] = load
                count += 1
            f.close()
        LOGS.info(
            f"{Symbols.bullet * 3} Loaded User Plugin: '{count}' {Symbols.bullet * 3}"
        )

    async def validate_logger(self, client: Client) -> bool:
        try:
            await client.get_chat_member(Config.LOGGER_ID, "me")
            return True
        except Exception:
            return await self.join_logger(client)

    async def join_logger(self, client: Client) -> bool:
        try:
            invite_link = await self.bot.export_chat_invite_link(Config.LOGGER_ID)
            await client.join_chat(invite_link)
            return True
        except Exception:
            return False

    async def start_message(self, version: dict) -> None:
        await self.bot.send_animation(
            Config.LOGGER_ID,
            "https://te.legra.ph/file/8deca5343c64d9db9401f.mp4",
            f"**{Symbols.check_mark} Jeweled Sword Zelretch is now online.**\n\n"
            f"**{Symbols.triangle_right} Clients:** `{len(self.users)}`\n"
            f"**{Symbols.triangle_right} Plugins:** `{len(Config.CMD_MENU)}`\n"
            f"**{Symbols.triangle_right} Commands:** `{len(Config.CMD_INFO)}`\n"
            f"**{Symbols.triangle_right} Stan Users:** `{len(Config.STAN_USERS)}`\n"
            f"**{Symbols.triangle_right} Auth Users:** `{len(Config.AUTH_USERS)}`\n\n"
            f"**{Symbols.triangle_right} Jeweled Sword Zelretch:** `{version['zelretch']}`\n"
            f"**{Symbols.triangle_right} Kurigram:** `{version['kurigram']}`\n"
            f"**{Symbols.triangle_right} Python:** `{version['python']}`",
            parse_mode=ParseMode.MARKDOWN,
            disable_notification=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Start Me", url=f"https://t.me/{self.bot.me.username}?start=start")]]
            ),
        )

    async def startup(self) -> None:
        LOGS.info(
            f"{Symbols.bullet * 3} Starting Jeweled Sword Zelretch Client & User {Symbols.bullet * 3}"
        )
        await self.start_bot()
        await self.start_user()
        await self.load_plugin()


class CustomMethods(ZelretchClient):
    async def input(self, message: Message) -> str:
        """Get the input from the user"""
        if len(message.command) < 2:
            output = ""

        else:
            try:
                output = message.text.split(" ", 1)[1].strip() or ""
            except IndexError:
                output = ""

        return output

    async def edit(
        self,
        message: Message,
        text: str,
        parse_mode: ParseMode = ParseMode.DEFAULT,
        no_link_preview: bool = True,
    ) -> Message:
        """Edit or Reply to a message, if possible"""
        if message.from_user and message.from_user.id in Config.STAN_USERS:
            if message.reply_to_message:
                return await message.reply_to_message.reply_text(
                    text,
                    parse_mode=parse_mode,
                    disable_web_page_preview=no_link_preview,
                )
            return await message.reply_text(
                text, parse_mode=parse_mode, disable_web_page_preview=no_link_preview
            )
        return await message.edit_text(
            text, parse_mode=parse_mode, disable_web_page_preview=no_link_preview
        )

    async def _delete(self, message: Message, delay: int = 0) -> None:
        """Delete a message after a certain period of time"""
        await asyncio.sleep(delay)
        await message.delete()

    async def delete(
        self, message: Message, text: str, delete: int = 10, in_background: bool = True
    ) -> None:
        """Edit a message and delete it after a certain period of time"""
        to_del = await self.edit(message, text)
        if in_background:
            asyncio.create_task(self._delete(to_del, delete))
        else:
            await self._delete(to_del, delete)

    async def error(self, message: Message, text: str, delete: int = 10) -> None:
        """Edit an error message and delete it after a certain period of time if mentioned"""
        to_del = await self.edit(message, f"{Symbols.cross_mark} **Error:** \n\n{text}")
        if delete:
            asyncio.create_task(self._delete(to_del, delete))

    async def _log(self, tag: str, text: str, file: str = None) -> None:
        """Log a message to the Logger Group"""
        msg = f"**#{tag.upper()}**\n\n{text}"
        try:
            if file:
                try:
                    await self.bot.send_document(Config.LOGGER_ID, file, caption=msg)
                except:
                    await self.bot.send_message(
                        Config.LOGGER_ID, msg, disable_web_page_preview=True
                    )
            else:
                await self.bot.send_message(
                    Config.LOGGER_ID, msg, disable_web_page_preview=True
                )
        except Exception as e:
            raise Exception(f"{Symbols.cross_mark} LogErr: {e}")

    async def check_and_log(self, tag: str, text: str, file: str = None) -> None:
        """Check if :
        \n-> the Logger Group is available
        \n-> the logging is enabled"""
        status = await db.get_env(ENV.is_logger)
        if status and status.lower() == "true":
            await self._log(tag, text, file)


zelretch = CustomMethods()
