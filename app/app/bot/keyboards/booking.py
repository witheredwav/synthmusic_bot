from datetime import date, time, timedelta
from decimal import Decimal

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callbacks import BookingActionCb, BookingCb, EngineerCb, NavCb
from app.db.models import Booking, EngineerProfile


def months_keyboard() -> InlineKeyboardBuilder:
    today = date.today().replace(day=1)
    builder = InlineKeyboardBuilder()
    for offset in range(4):
        month = today + timedelta(days=32 * offset)
        month = month.replace(day=1)
        builder.button(text=month.strftime("%m.%Y"), callback_data=BookingCb(action="month", value=month.isoformat()))
    builder.button(text="Отменить", callback_data=NavCb(target="menu"))
    builder.adjust(2, 1)
    return builder


def days_keyboard(month: date) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    cursor = month
    while cursor.month == month.month:
        if cursor >= date.today():
            builder.button(
                text=str(cursor.day),
                callback_data=BookingCb(action="day", value=cursor.isoformat()),
            )
        cursor += timedelta(days=1)
    builder.button(text="Назад", callback_data=BookingCb(action="back", value="month"))
    builder.adjust(7)
    return builder


def engineers_keyboard(engineers: list[EngineerProfile]) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for engineer in engineers:
        builder.button(
            text=f"{engineer.name} · {engineer.hourly_rate}/ч",
            callback_data=EngineerCb(action="select", engineer_id=engineer.id),
        )
    builder.button(text="Назад", callback_data=BookingCb(action="back", value="day"))
    builder.adjust(1)
    return builder


def times_keyboard(slots) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for slot in slots:
        builder.button(
            text=slot.strftime("%H:%M"),
            callback_data=BookingCb(action="time", value=slot.strftime("%H:%M")),
        )
    builder.button(text="Назад", callback_data=BookingCb(action="back", value="engineer"))
    builder.adjust(3)
    return builder


def night_times_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    slots = [time(hour, minute) for hour in range(0, 11) for minute in (0, 30)]
    slots.extend([time(22, 30), time(23, 0), time(23, 30)])
    for slot in slots:
        builder.button(
            text=slot.strftime("%H:%M"),
            callback_data=BookingCb(action="time", value=slot.strftime("%H:%M")),
        )
    builder.button(text="Назад", callback_data=BookingCb(action="back", value="day"))
    builder.adjust(3)
    return builder


def duration_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for hours in range(1, 7):
        label = f"{hours} час" if hours == 1 else f"{hours} часа" if hours < 5 else f"{hours} часов"
        builder.button(text=label, callback_data=BookingCb(action="duration", value=str(hours)))
    builder.button(text="Отменить", callback_data=NavCb(target="menu"))
    builder.adjust(2)
    return builder


def booking_decision_keyboard(booking: Booking, allow_contact: bool = False) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Подтвердить", callback_data=BookingActionCb(action="confirm", booking_id=booking.id))
    builder.button(text="❌ Отклонить", callback_data=BookingActionCb(action="reject", booking_id=booking.id))
    if allow_contact and booking.engineer.user.username:
        builder.button(text="Связаться", url=f"https://t.me/{booking.engineer.user.username}")
    builder.adjust(1)
    return builder


def client_booking_keyboard(booking: Booking) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    if booking.status.value in {"confirmed", "pending_manual"} and booking.engineer.user.username:
        builder.button(text="Связаться со звукорежиссером", url=f"https://t.me/{booking.engineer.user.username}")
    if booking.status.value in {"pending_engineer", "pending_manual", "confirmed"}:
        builder.button(text="Отменить запись", callback_data=BookingActionCb(action="cancel", booking_id=booking.id))
    builder.adjust(1)
    return builder


def booking_summary(data: dict, engineer: EngineerProfile) -> str:
    duration = int(data["duration_hours"])
    total = Decimal(duration) * engineer.hourly_rate
    return "\n".join(
        [
            "<b>Проверьте запись</b>",
            f"Дата: {data['day']}",
            f"Время: {data['time']}",
            f"Звукорежиссер: {engineer.name}",
            f"Продолжительность: {duration} ч",
            f"Стоимость: {total}",
            f"Имя: {data['client_name']}",
            f"Телефон: {data['client_phone']}",
        ]
    )
