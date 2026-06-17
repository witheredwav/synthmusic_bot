import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.types import BufferedInputFile
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.enums import BookingStatus
from app.db.models import Booking, ClientProfile, EngineerProfile
from app.db.session import async_session_factory
from app.services.reports import monthly_report
from app.services.users import list_admin_telegram_ids

logger = logging.getLogger(__name__)


async def notify_booking_created(bot: Bot, booking: Booking) -> None:
    text = booking_card_text(booking)
    engineer_user = booking.engineer.user
    if engineer_user:
        await safe_send(bot, engineer_user.telegram_id, text)
    if booking.status == BookingStatus.PENDING_MANUAL:
        async with async_session_factory() as session:
            for admin_id in await list_admin_telegram_ids(session):
                await safe_send(bot, admin_id, text)


async def safe_send(bot: Bot, chat_id: int, text: str, **kwargs) -> None:
    try:
        await bot.send_message(chat_id, text, **kwargs)
    except Exception:
        logger.exception("Failed to send Telegram message to %s", chat_id)


def booking_card_text(booking: Booking) -> str:
    return "\n".join(
        [
            f"<b>Заявка #{booking.id}</b>",
            f"Статус: {booking.status.value}",
            f"Дата: {booking.starts_at:%d.%m.%Y}",
            f"Время: {booking.starts_at:%H:%M}",
            f"Длительность: {booking.duration_hours} ч",
            f"Клиент: {booking.client_name}",
            f"Телефон: {booking.client_phone}",
            f"Стоимость: {booking.total_price}",
        ]
    )


async def send_due_reminders(bot: Bot) -> None:
    settings = get_settings()
    now = datetime.now(ZoneInfo(settings.timezone))
    async with async_session_factory() as session:
        result = await session.execute(
            select(Booking)
            .where(Booking.status == BookingStatus.CONFIRMED, Booking.starts_at > now)
            .options(
                selectinload(Booking.client).selectinload(ClientProfile.user),
                selectinload(Booking.engineer).selectinload(EngineerProfile.user),
            )
        )
        for booking in result.scalars():
            delta = booking.starts_at - now
            for hours in settings.reminder_hours:
                marker = "reminder_24h_sent_at" if hours == 24 else "reminder_2h_sent_at"
                already_sent = getattr(booking, marker)
                if already_sent is None and timedelta(0) <= delta <= timedelta(hours=hours):
                    await send_booking_reminder(bot, booking, hours)
                    setattr(booking, marker, now)
        await session.commit()


async def send_booking_reminder(bot: Bot, booking: Booking, hours: int) -> None:
    text = (
        f"Напоминание: запись через {hours} ч.\n"
        f"{booking.starts_at:%d.%m.%Y %H:%M}, {booking.duration_hours} ч."
    )
    await safe_send(bot, booking.client.user.telegram_id, text)
    await safe_send(bot, booking.engineer.user.telegram_id, f"Предстоящая запись:\n{text}")


async def send_monthly_report(bot: Bot) -> None:
    now = datetime.now(ZoneInfo(get_settings().timezone))
    tomorrow = now + timedelta(days=1)
    if tomorrow.month == now.month:
        return
    async with async_session_factory() as session:
        text, pdf_bytes = await monthly_report(session)
        admins = await list_admin_telegram_ids(session)
    document = BufferedInputFile(pdf_bytes, filename=f"studio-report-{now:%Y-%m}.pdf")
    for admin_id in admins:
        await safe_send(bot, admin_id, text)
        try:
            await bot.send_document(admin_id, document)
        except Exception:
            logger.exception("Failed to send monthly PDF report")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=get_settings().timezone)
    scheduler.add_job(send_due_reminders, "interval", minutes=5, args=[bot])
    scheduler.add_job(send_monthly_report, "cron", hour=20, minute=0, args=[bot])
    return scheduler
