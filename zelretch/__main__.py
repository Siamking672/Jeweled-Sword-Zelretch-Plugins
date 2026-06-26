import asyncio

from pyrogram import idle

from zelretch import __version__
from zelretch.core import (
    Config,
    ForcesubSetup,
    GachaBotsSetup,
    TemplateSetup,
    UserSetup,
    db,
    zelretch,
)
from zelretch.functions.tools import initialize_git
from zelretch.functions.utility import BList, Flood, TGraph


async def main():
    await zelretch.startup()
    await db.connect()
    await UserSetup()
    await ForcesubSetup()
    await GachaBotsSetup()
    await TemplateSetup()
    await Flood.updateFromDB()
    await BList.updateBlacklists()
    await TGraph.setup()
    await initialize_git(Config.PLUGINS_REPO)
    await zelretch.start_message(__version__)
    await idle()


if __name__ == "__main__":
    asyncio.run(main())
