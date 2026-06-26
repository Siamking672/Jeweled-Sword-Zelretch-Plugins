from pyrogram import Client, filters
from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)

from ..btnsG import gen_inline_keyboard, start_button
from ..btnsK import session_keyboard
from . import START_MSG, BotHelp, Config, Symbols, db, zelretch


@zelretch.bot.on_message(
    filters.command("session") & Config.AUTH_USERS & filters.private
)
async def session_menu(_, message: Message):
    await message.reply_text(
        "**🍀 𝖯𝗅𝖾𝖺𝗌𝖾 𝖼𝗁𝗈𝗈𝗌𝖾 𝖺𝗇 𝗈𝗉𝗍𝗂𝗈𝗇 𝖿𝗋𝗈𝗆 𝖻𝖾𝗅𝗈𝗐:**",
        reply_markup=session_keyboard(),
    )


@zelretch.bot.on_message(filters.regex(r"New 💫") & Config.AUTH_USERS & filters.private)
async def new_session(_, message: Message):
    await message.reply_text(
        "**𝖮𝗄𝖺𝗒!** 𝖫𝖾𝗍'𝗌 𝗌𝖾𝗍𝗎𝗉 𝖺 𝗇𝖾𝗐 𝗌𝖾𝗌𝗌𝗂𝗈𝗇",
        reply_markup=ReplyKeyboardRemove(),
    )

    phone_number = await zelretch.bot.ask(
        message.chat.id,
        "**1.** 𝖤𝗇𝗍𝖾𝗋 𝗒𝗈𝗎𝗋 𝗍𝖾𝗅𝖾𝗀𝗋𝖺𝗆 𝖺𝖼𝖼𝗈𝗎𝗇𝗍 𝗉𝗁𝗈𝗇𝖾 𝗇𝗎𝗆𝖻𝖾𝗋 𝗍𝗈 𝖺𝖽𝖽 𝗍𝗁𝖾 𝗌𝖾𝗌𝗌𝗂𝗈𝗇: \n\n__𝖲𝖾𝗇𝖽 /cancel 𝗍𝗈 𝖼𝖺𝗇𝖼𝖾𝗅 𝗍𝗁𝖾 𝗈𝗉𝖾𝗋𝖺𝗍𝗂𝗈𝗇.__",
        filters=filters.text,
        timeout=120,
    )

    if phone_number.text == "/cancel":
        return await message.reply_text("**𝖢𝖺𝗇𝖼𝖾𝗅𝗅𝖾𝖽!**")
    elif not phone_number.text.startswith("+") and not phone_number.text[1:].isdigit():
        return await message.reply_text(
            "**𝖤𝗋𝗋𝗈𝗋!** 𝖯𝗁𝗈𝗇𝖾 𝗇𝗎𝗆𝖻𝖾𝗋 𝗆𝗎𝗌𝗍 𝖻𝖾 𝗂𝗇 𝖽𝗂𝗀𝗂𝗍𝗌 𝖺𝗇𝖽 𝗌𝗁𝗈𝗎𝗅𝖽 𝖼𝗈𝗇𝗍𝖺𝗂𝗇 𝖼𝗈𝗎𝗇𝗍𝗋𝗒 𝖼𝗈𝖽𝖾."
        )

    try:
        client = Client(
            name="JeweledSwordZelretchSession",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            in_memory=True,
        )
        await client.connect()

        code = await client.send_code(phone_number.text)
        ask_otp = await zelretch.bot.ask(
            message.chat.id,
            "**2.** 𝖤𝗇𝗍𝖾𝗋 𝗍𝗁𝖾 𝖮𝖳𝖯 𝗌𝖾𝗇𝗍 𝗍𝗈 𝗒𝗈𝗎𝗋 𝗍𝖾𝗅𝖾𝗀𝗋𝖺𝗆 𝖺𝖼𝖼𝗈𝗎𝗇𝗍 𝖻𝗒 𝗌𝖾𝗉𝖺𝗋𝖺𝗍𝗂𝗇𝗀 𝖾𝗏𝖾𝗋𝗒 𝗇𝗎𝗆𝖻𝖾𝗋 𝗐𝗂𝗍𝗁 𝖺 𝗌𝗉𝖺𝖼𝖾. \n\n**𝖤𝗑𝖺𝗆𝗉𝗅𝖾:** `2 4 1 7 4`\n\n__𝖲𝖾𝗇𝖽 /cancel 𝗍𝗈 𝖼𝖺𝗇𝖼𝖾𝗅 𝗍𝗁𝖾 𝗈𝗉𝖾𝗋𝖺𝗍𝗂𝗈𝗇.__",
            filters=filters.text,
            timeout=300,
        )
        if ask_otp.text == "/cancel":
            return await message.reply_text("**𝖢𝖺𝗇𝖼𝖾𝗅𝗅𝖾𝖽!**")
        otp = ask_otp.text.replace(" ", "")

        try:
            await client.sign_in(phone_number.text, code.phone_code_hash, otp)
        except SessionPasswordNeeded:
            two_step_pass = await zelretch.bot.ask(
                message.chat.id,
                "**3.** 𝖤𝗇𝗍𝖾𝗋 𝗒𝗈𝗎𝗋 𝗍𝗐𝗈 𝗌𝗍𝖾𝗉 𝗏𝖾𝗋𝗂𝖿𝗂𝖼𝖺𝗍𝗂𝗈𝗇 𝗉𝖺𝗌𝗌𝗐𝗈𝗋𝖽: \n\n__𝖲𝖾𝗇𝖽 /cancel 𝗍𝗈 𝖼𝖺𝗇𝖼𝖾𝗅 𝗍𝗁𝖾 𝗈𝗉𝖾𝗋𝖺𝗍𝗂𝗈𝗇.__",
                filters=filters.text,
                timeout=120,
            )
            if two_step_pass.text == "/cancel":
                return await message.reply_text("**𝖢𝖺𝗇𝖼𝖾𝗅𝗅𝖾𝖽!**")
            await client.check_password(two_step_pass.text)

        session_string = await client.export_session_string()
        await message.reply_text(
            f"**𝖲𝗎𝖼𝖼𝖾𝗌𝗌!** 𝖸𝗈𝗎𝗋 𝗌𝖾𝗌𝗌𝗂𝗈𝗇 𝗌𝗍𝗋𝗂𝗇𝗀 𝗂𝗌 𝗀𝖾𝗇𝖾𝗋𝖺𝗍𝖾𝖽. 𝖠𝖽𝖽𝗂𝗇𝗀 𝗂𝗍 𝗍𝗈 𝖽𝖺𝗍𝖺𝖻𝖺𝗌𝖾..."
        )
        user_id = (await client.get_me()).id
        await db.update_session(user_id, session_string)
        await client.disconnect()
        await message.reply_text(
            "**𝖲𝗎𝖼𝖼𝖾𝗌𝗌!** 𝖲𝖾𝗌𝗌𝗂𝗈𝗇 𝗌𝗍𝗋𝗂𝗇𝗀 𝖺𝖽𝖽𝖾𝖽 𝗍𝗈 𝖽𝖺𝗍𝖺𝖻𝖺𝗌𝖾. 𝖸𝗈𝗎 𝖼𝖺𝗇 𝗇𝗈𝗐 𝗎𝗌𝖾 Jeweled Sword Zelretch 𝗈𝗇 𝗍𝗁𝗂𝗌 𝖺𝖼𝖼𝗈𝗎𝗇𝗍 𝖺𝖿𝗍𝖾𝗋 𝗋𝖾𝗌𝗍𝖺𝗋𝗍𝗂𝗇𝗀 𝗍𝗁𝖾 𝖻𝗈𝗍.\n\n**𝖭𝖮𝖳𝖤:** 𝖥𝗈𝗋 𝗌𝖾𝖼𝗎𝗋𝗂𝗍𝗒 𝗉𝗎𝗋𝗉𝗈𝗌𝖾𝗌 𝗇𝗈𝖻𝗈𝖽𝗒 𝗐𝗂𝗅𝗅 𝗁𝖺𝗏𝖾 𝗍𝗁𝖾 𝖺𝖼𝖼𝖾𝗌𝗌 𝗍𝗈 𝗒𝗈𝗎𝗋 𝗌𝖾𝗌𝗌𝗂𝗈𝗇 𝗌𝗍𝗋𝗂𝗇𝗀. 𝖭𝗈𝗍 𝖾𝗏𝖾𝗇 𝗒𝗈𝗎 𝗈𝗋 𝗍𝗁𝖾 𝖻𝗈𝗍."
        )
    except TimeoutError:
        await message.reply_text(
            "**𝖳𝗂𝗆𝖾𝗈𝗎𝗍𝖤𝗋𝗋𝗈𝗋!** 𝖸𝗈𝗎 𝗍𝗈𝗈𝗄 𝗅𝗈𝗇𝗀𝖾𝗋 𝗍𝗁𝖺𝗇 𝖾𝗑𝖼𝗉𝖾𝖼𝗍𝖾𝖽 𝗍𝗈 𝖼𝗈𝗆𝗉𝗅𝖾𝗍𝖾 𝗍𝗁𝖾 𝗉𝗋𝗈𝖼𝖾𝗌𝗌. 𝖯𝗅𝖾𝖺𝗌𝖾 𝗍𝗋𝗒 𝖺𝗀𝖺𝗂𝗇."
        )
    except Exception as e:
        await message.reply_text(f"**𝖤𝗋𝗋𝗈𝗋!** {e}")


@zelretch.bot.on_message(
    filters.regex(r"Delete ❌") & Config.AUTH_USERS & filters.private
)
async def delete_session(_, message: Message):
    all_sessions = await db.get_all_sessions()
    if not all_sessions:
        return await message.reply_text("𝖭𝗈 𝗌𝖾𝗌𝗌𝗂𝗈𝗇𝗌 𝖿𝗈𝗎𝗇𝖽 𝗂𝗇 𝖽𝖺𝗍𝖺𝖻𝖺𝗌𝖾.")

    collection = []
    for i in all_sessions:
        collection.append((i["user_id"], f"rm_session:{i['user_id']}"))

    buttons = gen_inline_keyboard(collection, 2)
    buttons.append([InlineKeyboardButton("Cancel ❌", "auth_close")])

    await message.reply_text(
        "**𝖢𝗁𝗈𝗈𝗌𝖾 𝖺 𝗌𝖾𝗌𝗌𝗂𝗈𝗇 𝗍𝗈 𝖽𝖾𝗅𝖾𝗍𝖾:**",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@zelretch.bot.on_callback_query(filters.regex(r"rm_session"))
async def rm_session_cb(client: Client, cb: CallbackQuery):
    collection = []
    user_id = int(cb.data.split(":")[1])
    all_sessions = await db.get_all_sessions()

    if not all_sessions:
        return await cb.message.delete()

    try:
        owner = await client.get_users(Config.OWNER_ID)
        owner_id = owner.id
        owner_name = owner.first_name
    except:
        owner_id = Config.OWNER_ID
        owner_name = "𝖮𝗐𝗇𝖾𝗋"
    if cb.from_user.id not in [user_id, owner_id]:
        return await cb.answer(
            f"𝖠𝖼𝖼𝖾𝗌𝗌 𝗋𝖾𝗌𝗍𝗋𝗂𝖼𝗍𝖾𝖽 𝗍𝗈 𝖺𝗇𝗈𝗍𝗁𝖾𝗋 𝗎𝗌𝖾𝗋𝗌. Only {owner_name} and session client can delete this session!",
            show_alert=True,
        )

    await db.rm_session(user_id)
    await cb.answer("**𝖲𝗎𝖼𝖼𝖾𝗌𝗌!** 𝖲𝖾𝗌𝗌𝗂𝗈𝗇 𝖽𝖾𝗅𝖾𝗍𝖾𝖽 𝖿𝗋𝗈𝗆 𝖽𝖺𝗍𝖺𝖻𝖺𝗌𝖾. \n__Restart the bot to apply changes.__", show_alert=True)

    for i in all_sessions:
        collection.append((i["user_id"], f"rm_session:{i['user_id']}"))

    buttons = gen_inline_keyboard(collection, 2)
    buttons.append([InlineKeyboardButton("Cancel ❌", "auth_close")])

    await cb.message.edit_reply_markup(InlineKeyboardMarkup(buttons))


@zelretch.bot.on_message(filters.regex(r"List 📜") & Config.AUTH_USERS & filters.private)
async def list_sessions(_, message: Message):
    all_sessions = await db.get_all_sessions()
    if not all_sessions:
        return await message.reply_text("𝖭𝗈 𝗌𝖾𝗌𝗌𝗂𝗈𝗇𝗌 𝖿𝗈𝗎𝗇𝖽 𝗂𝗇 𝖽𝖺𝗍𝖺𝖻𝖺𝗌𝖾.")

    text = f"**{Symbols.cross_mark} 𝖫𝗂𝗌𝗍 𝗈𝖿 𝗌𝖾𝗌𝗌𝗂𝗈𝗇𝗌:**\n\n"
    for i, session in enumerate(all_sessions):
        text += f"[{'0' if i <= 9 else ''}{i+1}] {Symbols.bullet} **𝖴𝗌𝖾𝗋 𝖨𝖣:** `{session['user_id']}`\n"

    await message.reply_text(text)


@zelretch.bot.on_message(filters.regex(r"Home 🏠") & filters.private & Config.AUTH_USERS)
async def go_home(_, message: Message):
    await message.reply_text(
        "**Home 🏠**",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.reply_text(
        START_MSG.format(message.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(start_button()),
    )


BotHelp("Sessions").add(
    "session", "This command is packed with tools to manage userbot sessions."
).info(
    "Session 🚀"
).done()
