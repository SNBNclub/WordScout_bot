from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def get_add_filter_ikb() -> InlineKeyboardMarkup:
    ikb = [
        [InlineKeyboardButton(text="отмена", callback_data="cancel_add_filter")],
    ]
    ikeyboard = InlineKeyboardMarkup(inline_keyboard=ikb)
    return ikeyboard
