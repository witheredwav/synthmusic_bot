from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.db.enums import Role
from app.db.models import User
from app.db.functions import get_user, create_user
from app.bot.keyboards.common import admin_menu, engineer_menu, client_menu

router = Router()


@router.message(CommandStart())
async def start(message: Message, db_user: User | None):

    user_id = message.from_user.id
    username = message.from_user.username

    if not db_user:
        db_user = await create_user(user_id, username)

    if db_user.has_role(Role.ADMIN):
        await message.answer("🔧 Админ панель", reply_markup=admin_menu())

    elif db_user.has_role(Role.ENGINEER):
        await message.answer("🎛 Инженер панель", reply_markup=engineer_menu())

    else:
        await message.answer("👋 Клиент панель", reply_markup=client_menu())
