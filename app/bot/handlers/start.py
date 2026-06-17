from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.common import admin_menu, client_menu, engineer_menu
from app.db.enums import Role
from app.db.models import User

router = Router()


@router.message(CommandStart())
async def start(message: Message, db_user: User):

    if not db_user:
        await message.answer("❌ Пользователь не найден в базе.")
        return

    if db_user.has_role(Role.ADMIN):
        await message.answer("Админ-панель открыта.", reply_markup=admin_menu())

    elif db_user.has_role(Role.ENGINEER):
        await message.answer("Кабинет звукорежиссера открыт.", reply_markup=engineer_menu())

    else:
        await message.answer("Добро пожаловать в студию.", reply_markup=client_menu())


@router.message(F.text == "Помощь")
async def help_message(message: Message):
    await message.answer(
        "Выберите нужный раздел кнопками меню."
    )
