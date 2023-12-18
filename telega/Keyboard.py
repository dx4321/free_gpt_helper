# Кнопки главного меню
#   Профиль, Модель

#
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def get_delete_keyboard():
    del_kb = InlineKeyboardMarkup(row_width=1)
    button = InlineKeyboardButton(text='Удалить Ваш api ключ', callback_data="delete_kb")
    del_kb.add(button)
    return del_kb
