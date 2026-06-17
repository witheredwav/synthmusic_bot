from datetime import date, datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, KeyboardButton, Message, ReplyKeyboardMarkup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.callbacks import BookingCb, ConfirmCb, EngineerCb, NavCb
from app.bot.keyboards.booking import (
    booking_summary,
    days_keyboard,
    duration_keyboard,
    engineers_keyboard,
    months_keyboard,
    night_times_keyboard,
    times_keyboard,
)
from app.bot.keyboards.common import client_menu, confirm_keyboard
from app.bot.states import BookingFlow, NightBookingFlow
from app.db.models import ClientProfile, EngineerProfile, User
from app.services.booking import BookingError, create_booking, get_booking
from app.services.notifications import notify_booking_created
from app.services.schedule import active_engineers, available_slots, slot_range

router = Router()


@router.message(F.text == "Записаться")
async def regular_booking_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(BookingFlow.month)
    await message.answer("Выберите месяц:", reply_markup=months_keyboard().as_markup())


@router.callback_query(BookingFlow.month, BookingCb.filter(F.action == "month"))
async def regular_month(callback: CallbackQuery, callback_data: BookingCb, state: FSMContext) -> None:
    month = date.fromisoformat(callback_data.value)
    await state.update_data(month=month.isoformat())
    await state.set_state(BookingFlow.day)
    await callback.message.edit_text("Выберите дату:", reply_markup=days_keyboard(month).as_markup())
    await callback.answer()


@router.callback_query(BookingFlow.day, BookingCb.filter(F.action == "day"))
async def regular_day(
    callback: CallbackQuery,
    callback_data: BookingCb,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    await state.update_data(day=callback_data.value)
    engineers = await active_engineers(session)
    if not engineers:
        await callback.answer("Нет доступных звукорежиссеров.", show_alert=True)
        return
    await state.set_state(BookingFlow.engineer)
    await callback.message.edit_text(
        "Выберите звукорежиссера:",
        reply_markup=engineers_keyboard(engineers).as_markup(),
    )
    await callback.answer()


@router.callback_query(BookingFlow.engineer, EngineerCb.filter(F.action == "select"))
async def regular_engineer(
    callback: CallbackQuery,
    callback_data: EngineerCb,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    data = await state.get_data()
    day = date.fromisoformat(data["day"])
    engineer = await session.get(EngineerProfile, callback_data.engineer_id)
    if engineer is None:
        await callback.answer("Звукорежиссер не найден.", show_alert=True)
        return
    await state.update_data(engineer_id=engineer.id)
    slots = await available_slots(session, engineer, day, duration_hours=1)
    if not slots:
        await callback.message.edit_text("На эту дату нет свободных слотов.")
        await callback.answer()
        return
    await state.set_state(BookingFlow.time)
    await callback.message.edit_text(
        f"{engineer.name}\n{engineer.short_description}\nСтоимость: {engineer.hourly_rate}/ч\n\nВыберите время:",
        reply_markup=times_keyboard(slots).as_markup(),
    )
    await callback.answer()


@router.callback_query(BookingFlow.time, BookingCb.filter(F.action == "time"))
async def regular_time(
    callback: CallbackQuery,
    callback_data: BookingCb,
    state: FSMContext,
    db_user: User,
) -> None:
    await state.update_data(time=callback_data.value)
    client = db_user.client_profile
    if client and client.display_name:
        await state.update_data(client_name=client.display_name)
        await ask_phone_or_duration(callback.message, state, client.phone)
    else:
        await state.set_state(BookingFlow.name)
        await callback.message.edit_text("Введите ваше имя.")
    await callback.answer()


@router.message(BookingFlow.name)
async def regular_name(message: Message, state: FSMContext) -> None:
    await state.update_data(pending_name=message.text.strip())
    await message.answer(
        f"Введенное имя: {message.text.strip()}",
        reply_markup=confirm_keyboard().as_markup(),
    )


@router.callback_query(BookingFlow.name, ConfirmCb.filter())
async def confirm_name(callback: CallbackQuery, callback_data: ConfirmCb, state: FSMContext) -> None:
    if callback_data.action == "cancel":
        await state.clear()
        await callback.message.edit_text("Запись отменена.")
    elif callback_data.action == "edit":
        await callback.message.edit_text("Введите имя заново.")
    else:
        data = await state.get_data()
        await state.update_data(client_name=data["pending_name"])
        await ask_phone_or_duration(callback.message, state, None)
    await callback.answer()


async def ask_phone_or_duration(message: Message, state: FSMContext, phone: str | None) -> None:
    if phone:
        await state.update_data(client_phone=phone)
        await state.set_state(BookingFlow.duration)
        await message.answer("Выберите длительность записи:", reply_markup=duration_keyboard().as_markup())
        return
    await state.set_state(BookingFlow.phone)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить телефон", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.answer("Отправьте номер телефона через кнопку Telegram Contact или вручную.", reply_markup=keyboard)


@router.message(BookingFlow.phone)
async def regular_phone(message: Message, state: FSMContext) -> None:
    phone = message.contact.phone_number if message.contact else message.text.strip()
    await state.update_data(pending_phone=phone)
    await message.answer(f"Введенный номер: {phone}", reply_markup=confirm_keyboard().as_markup())


@router.callback_query(BookingFlow.phone, ConfirmCb.filter())
async def confirm_phone(callback: CallbackQuery, callback_data: ConfirmCb, state: FSMContext) -> None:
    if callback_data.action == "cancel":
        await state.clear()
        await callback.message.edit_text("Запись отменена.")
    elif callback_data.action == "edit":
        await callback.message.edit_text("Введите телефон заново.")
    else:
        data = await state.get_data()
        await state.update_data(client_phone=data["pending_phone"])
        await state.set_state(BookingFlow.duration)
        await callback.message.answer("Выберите длительность записи:", reply_markup=duration_keyboard().as_markup())
    await callback.answer()


@router.callback_query(BookingFlow.duration, BookingCb.filter(F.action == "duration"))
async def regular_duration(
    callback: CallbackQuery,
    callback_data: BookingCb,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    duration = int(callback_data.value)
    await state.update_data(duration_hours=duration)
    data = await state.get_data()
    engineer = await session.get(EngineerProfile, data["engineer_id"])
    await state.set_state(BookingFlow.final_confirm)
    if duration >= 3:
        await callback.message.answer(
            "Записи от 3 часов требуют предварительного согласования со звукорежиссером или администратором."
        )
    await callback.message.answer(
        booking_summary(data | {"duration_hours": duration}, engineer),
        reply_markup=confirm_keyboard().as_markup(),
    )
    await callback.answer()


@router.callback_query(BookingFlow.final_confirm, ConfirmCb.filter())
async def regular_final(
    callback: CallbackQuery,
    callback_data: ConfirmCb,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    if callback_data.action == "cancel":
        await state.clear()
        await callback.message.edit_text("Запись отменена.", reply_markup=None)
        await callback.answer()
        return
    if callback_data.action == "edit":
        await state.set_state(BookingFlow.month)
        await callback.message.edit_text("Выберите месяц:", reply_markup=months_keyboard().as_markup())
        await callback.answer()
        return

    data = await state.get_data()
    client = await session.get(ClientProfile, db_user.client_profile.id)
    try:
        booking = await create_booking(
            session=session,
            client=client,
            engineer_id=data["engineer_id"],
            day=date.fromisoformat(data["day"]),
            clock=datetime.strptime(data["time"], "%H:%M").time(),
            duration_hours=int(data["duration_hours"]),
            client_name=data["client_name"],
            client_phone=data["client_phone"],
        )
        await session.commit()
        booking = await get_booking(session, booking.id)
        await notify_booking_created(callback.bot, booking)
    except BookingError as exc:
        await session.rollback()
        await callback.message.edit_text(str(exc))
        await callback.answer()
        return
    await state.clear()
    await callback.message.edit_text("Заявка создана. Вы получите уведомление после подтверждения.")
    await callback.message.answer("Главное меню", reply_markup=client_menu())
    await callback.answer()


@router.message(F.text == "Ночная запись")
async def night_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    engineers = await active_engineers(session)
    await state.set_state(NightBookingFlow.engineer)
    await message.answer(
        "Ночная запись доступна только по предварительному согласованию.\nВыберите звукорежиссера:",
        reply_markup=engineers_keyboard(engineers).as_markup(),
    )


@router.callback_query(NightBookingFlow.engineer, EngineerCb.filter(F.action == "select"))
async def night_engineer(callback: CallbackQuery, callback_data: EngineerCb, state: FSMContext) -> None:
    await state.update_data(engineer_id=callback_data.engineer_id)
    await state.set_state(NightBookingFlow.day)
    await callback.message.edit_text("Выберите месяц:", reply_markup=months_keyboard().as_markup())
    await callback.answer()


@router.callback_query(NightBookingFlow.day, BookingCb.filter(F.action == "month"))
async def night_month(callback: CallbackQuery, callback_data: BookingCb) -> None:
    month = date.fromisoformat(callback_data.value)
    await callback.message.edit_text("Выберите дату:", reply_markup=days_keyboard(month).as_markup())
    await callback.answer()


@router.callback_query(NightBookingFlow.day, BookingCb.filter(F.action == "day"))
async def night_day(callback: CallbackQuery, callback_data: BookingCb, state: FSMContext) -> None:
    await state.update_data(day=callback_data.value)
    await state.set_state(NightBookingFlow.time)
    await callback.message.edit_text("Выберите желаемое время:", reply_markup=night_times_keyboard().as_markup())
    await callback.answer()


@router.callback_query(NightBookingFlow.time, BookingCb.filter(F.action == "time"))
async def night_time(callback: CallbackQuery, callback_data: BookingCb, state: FSMContext) -> None:
    await state.update_data(time=callback_data.value)
    await state.set_state(NightBookingFlow.duration)
    await callback.message.edit_text("Выберите длительность:", reply_markup=duration_keyboard().as_markup())
    await callback.answer()


@router.callback_query(NightBookingFlow.duration, BookingCb.filter(F.action == "duration"))
async def night_duration(callback: CallbackQuery, callback_data: BookingCb, state: FSMContext) -> None:
    await state.update_data(duration_hours=int(callback_data.value))
    await state.set_state(NightBookingFlow.final_confirm)
    data = await state.get_data()
    await callback.message.answer(
        "\n".join(
            [
                "<b>Проверьте ночную заявку</b>",
                f"Дата: {data['day']}",
                f"Время: {data['time']}",
                f"Длительность: {data['duration_hours']} ч",
            ]
        ),
        reply_markup=confirm_keyboard().as_markup(),
    )
    await callback.answer()


@router.callback_query(NightBookingFlow.final_confirm, ConfirmCb.filter(F.action == "yes"))
async def night_final(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    data = await state.get_data()
    client = await session.get(ClientProfile, db_user.client_profile.id)
    name = client.display_name or db_user.first_name or "Клиент"
    phone = client.phone or "Не указан"
    try:
        booking = await create_booking(
            session=session,
            client=client,
            engineer_id=data["engineer_id"],
            day=date.fromisoformat(data["day"]),
            clock=datetime.strptime(data["time"], "%H:%M").time(),
            duration_hours=int(data["duration_hours"]),
            client_name=name,
            client_phone=phone,
            is_night=True,
        )
        await session.commit()
        booking = await get_booking(session, booking.id)
        await notify_booking_created(callback.bot, booking)
    except BookingError as exc:
        await session.rollback()
        await callback.message.edit_text(str(exc))
        await callback.answer()
        return
    await state.clear()
    await callback.message.edit_text("Ночная заявка создана и отправлена на согласование.")
    await callback.answer()


@router.callback_query(NavCb.filter(F.target == "menu"))
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("Главное меню", reply_markup=client_menu())
    await callback.answer()
