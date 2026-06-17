from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from app.bot.keyboards.common import admin_menu, client_menu, engineer_menu
from app.db.enums import Role
from app.db.models import User
from app.db.functions import get_user  # 👈 ВАЖНО: функция из БД

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    user_id = message.from_user.id

    # 🔥 получаем пользователя из базы
    db_user: User = await get_user(user_id)

    # 🔥 защита на случай если юзера нет
    if not db_user:
        await message.answer("Пользователь не найден в базе.")
        return

    # 🔥 логика ролей
    if db_user.has_role(Role.ADMIN):
        await message.answer("Админ-панель открыта.", reply_markup=admin_menu())

    elif db_user.has_role(Role.ENGINEER):
        await message.answer("Кабинет звукорежиссера открыт.", reply_markup=engineer_menu())

    else:
        await message.answer("Добро пожаловать в студию.", reply_markup=client_menu())


@router.message(F.text == "Помощь")
async def help_message(message: Message) -> None:
    await message.answer(
        "Выберите нужный раздел кнопками меню. Команды вручную вводить не нужно, "
        "кроме случаев, когда бот просит имя, телефон или Telegram ID."
    )
