from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.common import admin_menu, client_menu, engineer_menu
from app.db.enums import Role
from app.db.models import User
from app.db.functions import get_or_create_user

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    user_id = message.from_user.id
    username = message.from_user.username

    db_user: User = await get_or_create_user(user_id, username)

    if db_user.has_role(Role.ADMIN):
        await message.answer("Админ-панель открыта.", reply_markup=admin_menu())

    elif db_user.has_role(Role.ENGINEER):
        await message.answer("Кабинет звукорежиссера открыт.", reply_markup=engineer_menu())

    else:
        await message.answer("Добро пожаловать в студию.", reply_markup=client_menu())
