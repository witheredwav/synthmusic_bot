from collections.abc import Sequence

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callbacks import PageCb


PAGE_SIZE = 8


def paginate(items: Sequence, page: int = 0, page_size: int = PAGE_SIZE):
    start = page * page_size
    return items[start : start + page_size], max(0, (len(items) - 1) // page_size)


def add_pagination(builder: InlineKeyboardBuilder, target: str, page: int, total_pages: int) -> None:
    buttons = []
    if page > 0:
        buttons.append(("⬅️", PageCb(target=target, page=page - 1)))
    if page < total_pages:
        buttons.append(("➡️", PageCb(target=target, page=page + 1)))
    for text, callback in buttons:
        builder.button(text=text, callback_data=callback)

