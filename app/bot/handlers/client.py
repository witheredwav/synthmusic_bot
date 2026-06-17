from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.callbacks import BookingActionCb, EngineerCb, NavCb
from app.bot.keyboards.booking import client_booking_keyboard
from app.bot.keyboards.common import client_menu
from app.bot.keyboards.booking import engineers_keyboard
from app.config import get_settings
from app.db.enums import BookingStatus
from app.db.models import Booking, BonusLedger, ClientProfile, EngineerProfile, User
from app.services.booking import get_booking, set_booking_status
from app.services.notifications import booking_card_text
from app.services.schedule import active_engineers

router = Router()


@router.message(F.text == "Контакты студии")
async def contacts(message: Message) -> None:
    settings = get_settings()
    await message.answer(f"<b>{settings.studio_name}</b>\n{settings.studio_contacts}")


@router.message(F.text == "Наша команда")
async def team(message: Message, session: AsyncSession) -> None:
    engineers = await active_engineers(session)
    if not engineers:
        await message.answer("Команда пока не настроена.")
        return
    await message.answer("Выберите звукорежиссера:", reply_markup=engineers_keyboard(engineers).as_markup())


@router.callback_query(EngineerCb.filter(F.action == "select"))
async def engineer_card(callback: CallbackQuery, callback_data: EngineerCb, session: AsyncSession) -> None:
    engineer = await session.get(EngineerProfile, callback_data.engineer_id)
    if engineer is None:
        await callback.answer("Профиль не найден.", show_alert=True)
        return
    text = "\n".join(
        [
            f"<b>{engineer.name}</b>",
            engineer.full_description or engineer.short_description,
            f"Стоимость: {engineer.hourly_rate}/ч",
            f"Контакты: {engineer.contact_text}" if engineer.show_contacts and engineer.contact_text else "",
        ]
    )
    if engineer.photo_file_id:
        await callback.message.answer_photo(engineer.photo_file_id, caption=text)
    else:
        await callback.message.answer(text)
    await callback.answer()


@router.message(F.text == "Бонусы и рефералы")
async def bonuses(message: Message, db_user: User, session: AsyncSession) -> None:
    result = await session.execute(
        select(ClientProfile)
        .where(ClientProfile.user_id == db_user.id)
        .options(selectinload(ClientProfile.bonus_ledger))
    )
    client = result.scalar_one()
    link = f"https://t.me/{get_settings().bot_username}?start=ref_{client.referral_code}"
    await message.answer(
        "\n".join(
            [
                "<b>Бонусы и рефералы</b>",
                f"Ваша ссылка: {link}",
                f"Приглашено пользователей: {client.referrals_count}",
                f"Бонусные баллы: {client.bonus_points}",
                "Награды: 10 баллов - 1 час бесплатно или скидка 10%; 20 баллов - скидка 20%.",
            ]
        )
    )


@router.message(F.text == "Мои записи")
async def my_bookings(message: Message, db_user: User, session: AsyncSession) -> None:
    result = await session.execute(
        select(Booking)
        .join(ClientProfile)
        .where(ClientProfile.user_id == db_user.id)
        .options(selectinload(Booking.engineer).selectinload(EngineerProfile.user))
        .order_by(Booking.starts_at.desc())
        .limit(10)
    )
    bookings = list(result.scalars())
    if not bookings:
        await message.answer("У вас пока нет записей.", reply_markup=client_menu())
        return
    for booking in bookings:
        await message.answer(
            booking_card_text(booking),
            reply_markup=client_booking_keyboard(booking).as_markup(),
        )


@router.callback_query(BookingActionCb.filter(F.action == "cancel"))
async def cancel_booking(callback: CallbackQuery, callback_data: BookingActionCb, session: AsyncSession) -> None:
    booking = await get_booking(session, callback_data.booking_id)
    if booking is None:
        await callback.answer("Запись не найдена.", show_alert=True)
        return
    await set_booking_status(session, booking, BookingStatus.CANCELLED_BY_CLIENT)
    await session.commit()
    await callback.message.edit_text("Запись отменена.")
    await callback.answer()

