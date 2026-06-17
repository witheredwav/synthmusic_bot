from aiogram import Router, F
from aiogram.types import Message

from app.services.users import get_or_create_user
from app.enums.roles import Role

router = Router()


def _get_user_id(event: Message):
    return event.from_user.id


@router.message(F.text == "/start")
async def start(message: Message, db_user, session):
    tg_user = message.from_user
    tg_id = tg_user.id

    # 1. создаём или получаем пользователя
    db_user = await get_or_create_user(
        session=session,
        tg_id=tg_id,
        username=tg_user.username,
        full_name=tg_user.full_name,
    )

    # 2. проверка роли (ВАЖНО: теперь безопасно)
    is_admin = False

    try:
        if hasattr(db_user, "has_role"):
            is_admin = db_user.has_role(Role.ADMIN)
        elif isinstance(db_user, dict):
            is_admin = db_user.get("role") == "admin"
    except Exception:
        is_admin = False

    # 3. ответ пользователю
    if is_admin:
        await message.answer(
            "👋 Привет, админ!\n"
            "У тебя есть доступ к панели управления."
        )
    else:
        await message.answer(
            "👋 Привет!\n"
            "Ты зарегистрирован в системе."
        )
