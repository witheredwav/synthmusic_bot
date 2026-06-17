from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.bot.callbacks import BookingActionCb, ConfirmCb, NavCb
from app.bot.keyboards.admin import (
    bookings_list_keyboard,
    clients_keyboard,
    engineers_admin_keyboard,
    role_management_keyboard,
)
from app.bot.keyboards.booking import booking_decision_keyboard
from app.bot.keyboards.common import confirm_keyboard
from app.bot.states import AdminRoleFlow
from app.db.enums import BookingType, Role
from app.db.models import Booking, ClientProfile, EngineerProfile, User
from app.services.booking import get_booking
from app.services.stats import dashboard, revenue_by_engineer
from app.services.users import grant_role
from app.services.notifications import booking_card_text

router = Router()


def is_admin(user: User) -> bool:
    return user.has_role(Role.ADMIN)


# ---------------------------
# STATS
# ---------------------------
@router.message(F.text == "Статистика")
async def stats(message: Message, db_user: User, session: AsyncSession):
    if not is_admin(db_user):
        return

    await message.answer(await dashboard(session))
    await message.answer(await revenue_by_engineer(session))


# ---------------------------
# ROLE MENU
# ---------------------------
@router.message(F.text.in_({"Пользователи", "Администраторы"}))
async def users(message: Message, db_user: User):
    if not is_admin(db_user):
        return

    await message.answer(
        "Управление ролями:",
        reply_markup=role_management_keyboard().as_markup()
    )


# ---------------------------
# START ROLE FLOW
# ---------------------------
@router.callback_query(NavCb.filter(F.target.in_({"add_engineer", "add_admin"})))
async def role_start(
    callback: CallbackQuery,
    callback_data: NavCb,
    state: FSMContext,
    db_user: User,
):
    if not is_admin(db_user):
        await callback.answer("Нет доступа", show_alert=True)
        return

    role = Role.ENGINEER if callback_data.target == "add_engineer" else Role.ADMIN

    await state.set_state(AdminRoleFlow.telegram_id)
    await state.update_data(role=role.value)

    await callback.message.answer("Введите Telegram ID")
    await callback.answer()


# ---------------------------
# ENTER TELEGRAM ID
# ---------------------------
@router.message(AdminRoleFlow.telegram_id)
async def role_id(message: Message, state: FSMContext):
    try:
        telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer("Telegram ID должен быть числом")
        return

    await state.update_data(telegram_id=telegram_id)
    await state.set_state(AdminRoleFlow.confirm)

    await message.answer(
        f"Telegram ID: {telegram_id}",
        reply_markup=confirm_keyboard().as_markup()
    )


# ---------------------------
# CONFIRM ROLE
# ---------------------------
@router.callback_query(AdminRoleFlow.confirm, ConfirmCb.filter())
async def role_confirm(
    callback: CallbackQuery,
    callback_data: ConfirmCb,
    state: FSMContext,
    session: AsyncSession,
):
    if callback_data.action == "cancel":
        await state.clear()
        await callback.message.edit_text("Отменено")
        await callback.answer()
        return

    if callback_data.action == "edit":
        await state.set_state(AdminRoleFlow.telegram_id)
        await callback.message.edit_text("Введите Telegram ID заново")
        await callback.answer()
        return

    data = await state.get_data()
    role = Role(data["role"])

    await grant_role(session, data["telegram_id"], role)
    await session.commit()

    await state.clear()
    await callback.message.edit_text(f"Роль {role.value} назначена")
    await callback.answer()


# ---------------------------
# BOOKINGS LIST
# ---------------------------
@router.message(F.text.in_({"Все записи", "Ночные записи"}))
async def all_bookings(message: Message, db_user: User, session: AsyncSession):
    if not is_admin(db_user):
        return

    stmt = select(Booking).order_by(Booking.starts_at.desc()).limit(20)

    if message.text == "Ночные записи":
        stmt = stmt.where(Booking.booking_type == BookingType.NIGHT)

    result = await session.execute(stmt)
    bookings = list(result.scalars())

    if not bookings:
        await message.answer("Записей нет")
        return

    await message.answer(
        "Выберите запись:",
        reply_markup=bookings_list_keyboard(bookings).as_markup()
    )


# ---------------------------
# VIEW BOOKING
# ---------------------------
@router.callback_query(BookingActionCb.filter(F.action == "view"))
async def booking_view(
    callback: CallbackQuery,
    callback_data: BookingActionCb,
    session: AsyncSession,
    db_user: User,
):
    if not is_admin(db_user):
        await callback.answer("Нет доступа", show_alert=True)
        return

    booking = await get_booking(session, callback_data.booking_id)

    if booking is None:
        await callback.answer("Не найдено", show_alert=True)
        return

    await callback.message.answer(
        booking_card_text(booking),
        reply_markup=booking_decision_keyboard(
            booking,
            allow_contact=True
        ).as_markup()
    )

    await callback.answer()


# ---------------------------
# CLIENTS
# ---------------------------
@router.message(F.text == "Клиенты")
async def clients(message: Message, db_user: User, session: AsyncSession):
    if not is_admin(db_user):
        return

    result = await session.execute(
        select(ClientProfile)
        .options(selectinload(ClientProfile.user))
        .order_by(ClientProfile.created_at.desc())
        .limit(20)
    )

    clients_list = list(result.scalars())

    if not clients_list:
        await message.answer("Клиентов нет")
        return

    await message.answer(
        "Клиенты:",
        reply_markup=clients_keyboard(clients_list).as_markup()
    )


# ---------------------------
# CLIENT CARD
# ---------------------------
@router.callback_query(NavCb.filter(F.target.startswith("client_")))
async def client_card(
    callback: CallbackQuery,
    callback_data: NavCb,
    session: AsyncSession,
    db_user: User,
):
    if not is_admin(db_user):
        await callback.answer("Нет доступа", show_alert=True)
        return

    client_id = int(callback_data.target.split("_")[1])

    client = await session.get(
        ClientProfile,
        client_id,
        options=[selectinload(ClientProfile.user)]
    )

    if client is None:
        await callback.answer("Не найдено", show_alert=True)
        return

    await callback.message.answer(
        "\n".join([
            f"<b>Клиент #{client.id}</b>",
            f"Telegram ID: {client.user.telegram_id}",
            f"Username: @{client.user.username}" if client.user.username else "Username: -",
            f"Имя: {client.display_name or client.user.first_name or '-'}",
            f"Телефон: {client.phone or '-'}",
            f"Записей: {client.bookings_count}",
            f"Завершенных: {client.completed_bookings_count}",
            f"Отмен: {client.cancelled_bookings_count}",
            f"Рефералов: {client.referrals_count}",
            f"Бонусов: {client.bonus_points}",
        ])
    )

    await callback.answer()


# ---------------------------
# ENGINEERS
# ---------------------------
@router.message(F.text == "Звукорежиссеры")
async def engineers(message: Message, db_user: User, session: AsyncSession):
    if not is_admin(db_user):
        return

    result = await session.execute(
        select(EngineerProfile).order_by(EngineerProfile.name)
    )

    engineers_list = list(result.scalars())

    await message.answer(
        "Звукорежиссеры:",
        reply_markup=engineers_admin_keyboard(engineers_list).as_markup()
    )


# ---------------------------
# SETTINGS
# ---------------------------
@router.message(F.text.in_({"Бонусная система", "Настройки"}))
async def settings_hint(message: Message, db_user: User):
    if not is_admin(db_user):
        return

    await message.answer(
        "Бонусы, графики и настройки хранятся в БД. "
        "Все критические действия защищены подтверждением."
    )
