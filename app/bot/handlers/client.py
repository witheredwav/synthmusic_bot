from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from app.db.models import ClientProfile
from app.services.users import get_or_create_user

router = Router()


def _get_user_id(db_user):
    """
    Универсальный извлекатель user_id
    (потому что у тебя сейчас каша: dict / ORM / разные поля)
    """
    if db_user is None:
        return None

    if isinstance(db_user, dict):
        return db_user.get("id") or db_user.get("user_id")

    return getattr(db_user, "user_id", None) or getattr(db_user, "id", None)


@router.message(F.text == "👤 Профиль")
async def profile(message: Message, db_user, session):
    user_id = _get_user_id(db_user)

    if not user_id:
        await message.answer("Ошибка: пользователь не найден")
        return

    profile = await session.scalar(
        select(ClientProfile).where(ClientProfile.user_id == user_id)
    )

    if not profile:
        await message.answer("Профиль не найден")
        return

    await message.answer(
        f"👤 Профиль:\n"
        f"ID: {profile.user_id}\n"
        f"Бонусы: {profile.bonuses}\n"
        f"Статус: {profile.status}"
    )


@router.message(F.text == "🎁 Бонусы")
async def bonuses(message: Message, db_user, session):
    user_id = _get_user_id(db_user)

    if not user_id:
        await message.answer("Ошибка: пользователь не найден")
        return

    profile = await session.scalar(
        select(ClientProfile).where(ClientProfile.user_id == user_id)
    )

    if not profile:
        await message.answer("Профиль не найден")
        return

    await message.answer(f"🎁 Ваши бонусы: {profile.bonuses}")


@router.message(F.text == "📊 Статистика")
async def stats(message: Message, db_user, session):
    user_id = _get_user_id(db_user)

    if not user_id:
        await message.answer("Ошибка: пользователь не найден")
        return

    profile = await session.scalar(
        select(ClientProfile).where(ClientProfile.user_id == user_id)
    )

    if not profile:
        await message.answer("Нет данных")
        return

    await message.answer(
        f"📊 Статистика:\n"
        f"Бонусы: {profile.bonuses}\n"
        f"Статус: {profile.status}"
    )
