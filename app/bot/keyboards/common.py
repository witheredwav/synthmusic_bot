from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callbacks import ConfirmCb, NavCb


# =========================
# 📱 CLIENT MENU (Reply)
# =========================
def client_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Записаться"), KeyboardButton(text="Ночная запись")],
            [KeyboardButton(text="Наша команда"), KeyboardButton(text="Мои записи")],
            [KeyboardButton(text="Бонусы и рефералы")],
            [KeyboardButton(text="Контакты студии"), KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True
    )


# =========================
# 🎛 ENGINEER MENU (Reply)
# =========================
def engineer_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Новые заявки"), KeyboardButton(text="Ночные заявки")],
            [KeyboardButton(text="Мои записи"), KeyboardButton(text="Расписание")],
            [KeyboardButton(text="График работы")]
        ],
        resize_keyboard=True
    )


# =========================
# 🛠 ADMIN MENU (Reply)
# =========================
def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Статистика"), KeyboardButton(text="Все записи")],
            [KeyboardButton(text="Ночные записи"), KeyboardButton(text="Клиенты")],
            [KeyboardButton(text="Пользователи"), KeyboardButton(text="Звукорежиссеры")],
            [KeyboardButton(text="Администраторы"), KeyboardButton(text="Бонусная система")],
            [KeyboardButton(text="Наша команда"), KeyboardButton(text="Настройки")]
        ],
        resize_keyboard=True
    )


# =========================
# ✅ CONFIRM KEYBOARD (Inline)
# =========================
def confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="✅ Подтвердить", callback_data=ConfirmCb(action="yes"))
    builder.button(text="✏️ Изменить", callback_data=ConfirmCb(action="edit"))
    builder.button(text="❌ Отменить", callback_data=ConfirmCb(action="cancel"))

    builder.adjust(1)

    return builder.as_markup()


# =========================
# 🔙 BACK BUTTON (Inline)
# =========================
def back_keyboard(target: str = "menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="⬅️ Назад", callback_data=NavCb(target=target))

    return builder.as_markup()
