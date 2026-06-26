import os

import requests
from pyrogram.types import Message

from zelretch.core import ENV
from zelretch.functions.images import remove_bg
from zelretch.functions.media import get_media_text_ocr
from zelretch.functions.paste import spaceBin

from . import Config, HelpMenu, db, zelretch, on_message


@on_message("readimage", allow_stan=True)
async def readImage(_, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        return await zelretch.delete(message, "Reply to a photo to read text on it.")

    api_key = await db.get_env(ENV.ocr_api)
    if not api_key:
        return await zelretch.delete(
            message, "To read texts from images you need to setup OCR Space Api key."
        )

    language = "eng"
    if len(message.command) >= 2:
        language = message.command[1]

    hell = await zelretch.edit(message, "Reading image...")

    filename = await message.reply_to_message.download(Config.TEMP_DIR)
    text = get_media_text_ocr(filename, api_key, language)

    try:
        await zelretch.edit(hell, text["ParsedResults"][0]["ParsedText"])
    except Exception as e:
        await zelretch.error(hell, f"`{e}`")

    os.remove(filename)


@on_message(["removebg", "rmbg"], allow_stan=True)
async def removeBg(_, message: Message):
    api_key = await db.get_env(ENV.remove_bg_api)
    if not api_key:
        return await zelretch.delete(
            message, "To remove background you need to setup Remove BG Api key."
        )

    if message.reply_to_message:
        if (
            message.reply_to_message.document
            and message.reply_to_message.document.mime_type.lower().startswith("image")
        ):
            filename = await message.reply_to_message.download(Config.TEMP_DIR)
        elif message.reply_to_message.photo:
            filename = await message.reply_to_message.download(Config.TEMP_DIR)
        elif (
            message.reply_to_message.sticker
            and not message.reply_to_message.sticker.is_animated
            and not message.reply_to_message.sticker.is_video
        ):
            filename = await message.reply_to_message.download(Config.TEMP_DIR + "sticker.png")
        else:
            return await zelretch.delete(
                message, "Reply to an image or give the url to remove background."
            )
    elif len(message.command) >= 2:
        resp = requests.get(await zelretch.input(message))
        filename = f"{Config.TEMP_DIR}/{message.id}.png"

        with open(filename, "wb") as f:
            f.write(resp.content)
    else:
        return await zelretch.delete(
            message, "Reply to an image or give the url to remove background."
        )

    hell = await zelretch.edit(message, "Removing background...")

    try:
        removed_img = await remove_bg(api_key, filename)
        doc_file = await message.reply_document(
            removed_img,
            caption="💫 **Removed Background!**",
            force_document=True,
        )
        await doc_file.reply_photo(removed_img, caption="🖼️ **Preview!**")
        os.remove(filename)
        os.remove(removed_img)
    except Exception as e:
        await zelretch.error(hell, f"`{e}`")


@on_message("paste", allow_stan=True)
async def paste_text(_, message: Message):
    hell = await zelretch.edit(message, "Pasting text...")
    text_to_paste = ""
    extention = "none"

    if len(message.command) >= 2:
        text_to_paste = await zelretch.input(message)
    elif message.reply_to_message.text:
        text_to_paste = message.reply_to_message.text
    elif message.reply_to_message.document:
        filename = await message.reply_to_message.download(Config.TEMP_DIR)
        with open(filename, "r") as f:
            text_to_paste = f.read()
        extention = filename.split(".")[-1]
        os.remove(filename)
    else:
        return await zelretch.delete(message, "Reply to a text to paste it.")

    try:
        await hell.edit(
            f"**📝 Pasted to:** {spaceBin(text_to_paste, extention)}",
            disable_web_page_preview=True,
        )
    except Exception as e:
        await zelretch.error(hell, f"`{e}`")


@on_message("exchangerate", allow_stan=True)
async def currencyAPI(_, message: Message):
    if len(message.command) < 3:
        return await zelretch.delete(message, "Give currency code to get it's value.")

    from_code = message.command[1].upper()
    to_code = message.command[2].upper()

    apikey = await db.get_env(ENV.currency_api)
    if not apikey:
        return await zelretch.delete(message, "Please setup currency api key.")

    hell = await zelretch.edit(message, "Getting currency value...")
    url = "https://v6.exchangerate-api.com/v6/{0}/pair/{1}/{2}"

    resp = requests.get(url.format(apikey, from_code, to_code))
    data = resp.json()

    if data["result"] == "success":
        await zelretch.edit(
            hell,
            f"**💫 Currency Exchange Rate** \n\n**💰 {data['base_code']} to {data['target_code']}:** `{data['conversion_rate']}`\n\n**🕧 Updated At:** `{data['time_last_update_utc']} UTC`",
        )
    else:
        await zelretch.error(hell, f"**Error:** `{data['error-type']}`")


@on_message("currency", allow_stan=True)
async def currencyAPI2(_, message: Message):
    if len(message.command) < 4:
        return await zelretch.delete(
            message, "Give amount and currency codes to get it's value."
        )

    try:
        amount = float(message.command[1])
    except Exception:
        return await zelretch.delete(message, "Give amount in numbers.")

    from_code = message.command[2].upper()
    to_code = message.command[3].upper()

    apikey = await db.get_env(ENV.currency_api)
    if not apikey:
        return await zelretch.delete(message, "Please setup currency api key.")

    hell = await zelretch.edit(message, "Getting currency value...")
    url = "https://v6.exchangerate-api.com/v6/{0}/pair/{1}/{2}/{3}"

    resp = requests.get(url.format(apikey, from_code, to_code, amount))
    data = resp.json()

    if data["result"] == "success":
        await zelretch.edit(
            hell,
            f"**💫 Currency Exchange Rate** \n\n💰 `{amount} {data['base_code']}` = `{data['conversion_result']} {data['target_code']}` \n**📈 Conversion Rate:** `{data['conversion_rate']}`\n\n**🕧 Updated At:** `{data['time_last_update_utc']} UTC`",
        )
    else:
        await zelretch.error(hell, f"**Error:** `{data['error-type']}`")


@on_message("currencies", allow_stan=True)
async def currencyCodes(_, message: Message):
    hell = await zelretch.edit(message, "Getting currency codes...")

    apikey = await db.get_env(ENV.currency_api)
    if not apikey:
        return await zelretch.delete(hell, "Please setup currency api key.")

    url = "https://v6.exchangerate-api.com/v6/{0}/codes"
    resp = requests.get(url.format(apikey))
    data = resp.json()

    supported_codes: list = data["supported_codes"]
    outStr = "Supported Currency Codes:\n\n"
    for i, code in enumerate(supported_codes):
        outStr += f"{i+1})    {code[0]} - {code[1]}\n"

    paste_link = spaceBin(outStr)
    await hell.edit(
        f"**💫 Supported Currency Codes:** `{len(supported_codes)}` \n\n**📝 Paste Link:** {paste_link}",
        disable_web_page_preview=True,
    )


HelpMenu("utilities").add(
    "readimage",
    "<reply to message> <language code (optional)>",
    "Read the texts on the image and send it as a message.",
    "read eng",
    "Need to setup OCR Space Api key from https://ocr.space/ocrapi",
).add(
    "removebg",
    "<reply to image> or <image url>",
    "Remove the background of the image and send it as a document. You will need to setup Remove BG Api key.",
    "removebg https://example.com/image.png",
    "An alias of 'rmbg' is also available.\nNeed to setup Remove BG Api key from https://www.remove.bg/api",
).add(
    "paste",
    "<reply to message> or <text>",
    "Paste the text to spaceb.in and send the link.",
    "paste",
).add(
    "exchangerate",
    "<from currency code> <to currency code>",
    "Get the exchange rate of the given currency codes.",
    "exchangerate usd inr",
    "Need to setup currency api from https://www.exchangerate-api.com",
).add(
    "currency",
    "<amount> <from currency code> <to currency code>",
    "Get the exchange rate of the given currency codes.",
    "currency 10 usd inr",
    "Need to setup currency api from https://www.exchangerate-api.com",
).add(
    "currencies",
    None,
    "Get the list of supported currency codes.",
    "currencies",
    "Need to setup currency api from https://www.exchangerate-api.com",
).info(
    "Some utilities command!"
).done()
