from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.callbacks import BookingActionCb, NavCb
from app.db.models import Booking, ClientProfile, EngineerProfile


def role_management_keyboard() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Добавить звукорежиссера", callback_data=NavCb(target="add_engineer"))
    builder.button(text="Добавить администратора", callback_data=NavCb(target="add_admin"))
    builder.adjust(1)
    return builder


def bookings_list_keyboard(bookings: list[Booking]) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for booking in bookings:
        builder.button(
            text=f"#{booking.id} {booking.starts_at:%d.%m %H:%M} {booking.status.value}",
            callback_data=BookingActionCb(action="view", booking_id=booking.id),
        )
    builder.adjust(1)
    return builder


def clients_keyboard(clients: list[ClientProfile]) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for client in clients:
        builder.button(
            text=f"{client.display_name or client.user.first_name or client.user.telegram_id}",
            callback_data=NavCb(target=f"client_{client.id}"),
        )
    builder.adjust(1)
    return builder


def engineers_admin_keyboard(engineers: list[EngineerProfile]) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    for engineer in engineers:
        builder.button(text=engineer.name, callback_data=NavCb(target=f"engineer_{engineer.id}"))
    builder.adjust(1)
    return builder

