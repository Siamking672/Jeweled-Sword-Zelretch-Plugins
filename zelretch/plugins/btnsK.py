# K: Keyboard Buttons

from pyrogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup


def gen_keyboard(collection: list, row: int = 2) -> list[list[KeyboardButton]]:
    keyboard = []
    for i in range(0, len(collection), row):
        kyb = []
        for x in collection[i : i + row]:
            kyb.append(KeyboardButton(x))
        keyboard.append(kyb)
    return keyboard




def session_inline_keyboard() -> list[list[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton("New 💫", "session:new"),
            InlineKeyboardButton("Delete ❌", "session:delete"),
        ],
        [
            InlineKeyboardButton("List 📜", "session:list"),
            InlineKeyboardButton("Home 🏠", "session:home"),
        ],
    ]


def session_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("New 💫"),
                KeyboardButton("Delete ❌"),
            ],
            [
                KeyboardButton("List 📜"),
                KeyboardButton("Home 🏠"),
            ],
        ],
        resize_keyboard=True,
    )


def start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("📟 Session"),
                KeyboardButton("👥 Users"),
            ],
            [
                KeyboardButton("Others 📣"),
            ],
        ],
        resize_keyboard=True,
    )
