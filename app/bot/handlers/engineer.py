from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.bot.callbacks import BookingActionCb, ConfirmCb
from app.bot.keyboards.booking import booking_decision_keyboard
from app.bot.keyboards.common import confirm_keyboard, engineer_menu
from app.bot.states import RejectBookingFlow
from app.db.enums import BookingStatus, BookingType, Role
from app.db.models import Booking, EngineerProfile, User
from app.services.booking import get_booking, set_booking_status
from app.services.notifications import booking_card_text, safe_send

router = Router()


def is_engineer(user: User) -> bool:
    return user.has_role(Role.ENGINEER) or user.has_role(Role.ADMIN)


@router.message(F.text.in_({"Новые заявки", "Ночные заявки"}))
async def incoming_requests(message: Message, db_user: User, session: AsyncSession) -> None:
    if not is_engineer(db_user):
        return
    engineer = db_user.engineer_profile
    if engineer is None and not db_user.has_role(Role.ADMIN):
        await message.answer("Профиль звукорежиссера не найден.")
        return
    statement = (
        select(Booking)
        .options(selectinload(Booking.engineer).selectinload(EngineerProfile.user))
        .order_by(Booking.starts_at)
        .limit(20)
    )
    if message.text == "Ночные заявки":
        statement = statement.where(Booking.booking_type == BookingType.NIGHT)
    else:
        statement = statement.where(Booking.status.in_([BookingStatus.PENDING_ENGINEER, BookingStatus.PENDING_MANUAL]))
    if engineer is not None and not db_user.has_role(Role.ADMIN):
        statement = statement.where(Booking.engineer_id == engineer.id)
    result = await session.execute(statement)
    bookings = list(result.scalars())
    if not bookings:
        await message.answer("Новых заявок нет.", reply_markup=engineer_menu())
        return
    for booking in bookings:
        await message.answer(
            booking_card_text(booking),
            reply_markup=booking_decision_keyboard(booking, allow_contact=True).as_markup(),
        )


@router.message(F.text == "Расписание")
async def schedule(message: Message, db_user: User, session: AsyncSession) -> None:
    if not is_engineer(db_user):
        return
    engineer = db_user.engineer_profile
    if engineer is None:
        await message.answer("Для администратора откройте раздел «Все записи».")
        return
    result = await session.execute(
        select(Booking)
        .where(
            Booking.engineer_id == engineer.id,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING_MANUAL]),
        )
        .order_by(Booking.starts_at)
        .limit(20)
    )
    bookings = list(result.scalars())
    if not bookings:
        await message.answer("Расписание пустое.")
        return
    await message.answer("\n\n".join(booking_card_text(item) for item in bookings))


@router.callback_query(BookingActionCb.filter(F.action == "confirm"))
async def confirm_booking(callback: CallbackQuery, callback_data: BookingActionCb, session: AsyncSession) -> None:
    booking = await get_booking(session, callback_data.booking_id)
    if booking is None:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    await set_booking_status(session, booking, BookingStatus.CONFIRMED)
    await session.commit()
    await safe_send(
        callback.bot,
        booking.client.user.telegram_id,
        f"Ваша запись #{booking.id} подтверждена: {booking.starts_at:%d.%m.%Y %H:%M}.",
    )
    await callback.message.edit_text("Запись подтверждена.")
    await callback.answer()


@router.callback_query(BookingActionCb.filter(F.action == "reject"))
async def ask_reject_reason(
    callback: CallbackQuery,
    callback_data: BookingActionCb,
    state: FSMContext,
) -> None:
    await state.set_state(RejectBookingFlow.reason)
    await state.update_data(booking_id=callback_data.booking_id)
    await callback.message.answer("Введите причину отказа.")
    await callback.answer()


@router.message(RejectBookingFlow.reason)
async def reject_reason(message: Message, state: FSMContext) -> None:
    await state.update_data(reason=message.text.strip())
    await state.set_state(RejectBookingFlow.confirm)
    await message.answer(
        f"Причина отказа:\n{message.text.strip()}",
        reply_markup=confirm_keyboard().as_markup(),
    )


@router.callback_query(RejectBookingFlow.confirm, ConfirmCb.filter())
async def reject_final(
    callback: CallbackQuery,
    callback_data: ConfirmCb,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if callback_data.action == "cancel":
        await state.clear()
        await callback.message.edit_text("Отказ отменен.")
        await callback.answer()
        return
    if callback_data.action == "edit":
        await state.set_state(RejectBookingFlow.reason)
        await callback.message.edit_text("Введите причину отказа заново.")
        await callback.answer()
        return
    data = await state.get_data()
    booking = await get_booking(session, data["booking_id"])
    if booking is None:
        await callback.answer("Заявка не найдена.", show_alert=True)
        return
    await set_booking_status(session, booking, BookingStatus.REJECTED, data["reason"])
    await session.commit()
    await safe_send(
        callback.bot,
        booking.client.user.telegram_id,
        f"Запись #{booking.id} отклонена. Причина: {data['reason']}",
    )
    await state.clear()
    await callback.message.edit_text("Отказ отправлен клиенту.")
    await callback.answer()


@router.callback_query(BookingActionCb.filter(F.action.in_({"attended", "no_show"})))
async def mark_attendance(callback: CallbackQuery, callback_data: BookingActionCb, session: AsyncSession) -> None:
    booking = await get_booking(session, callback_data.booking_id)
    if booking is None:
        await callback.answer("Запись не найдена.", show_alert=True)
        return
    status = BookingStatus.ATTENDED if callback_data.action == "attended" else BookingStatus.NO_SHOW
    await set_booking_status(session, booking, status)
    await session.commit()
    await callback.message.edit_text("Статус обновлен.")
    await callback.answer()


@router.message(F.text == "График работы")
async def work_schedule_hint(message: Message, db_user: User) -> None:
    if not is_engineer(db_user):
        return
    await message.answer(
        "График задается администратором в таблицах work_intervals и days_off. "
        "После добавления интервалов клиент видит только доступные слоты."
    )

