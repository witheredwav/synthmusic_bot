from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import BookingStatus, BookingType, BonusDirection
from app.db.models import Booking, BonusLedger, ClientProfile, EngineerProfile, Referral


async def dashboard(session: AsyncSession) -> str:
    bookings_total = await scalar(session, select(func.count(Booking.id)))
    confirmed = await scalar(
        session,
        select(func.count(Booking.id)).where(Booking.status == BookingStatus.CONFIRMED),
    )
    night = await scalar(
        session,
        select(func.count(Booking.id)).where(Booking.booking_type == BookingType.NIGHT),
    )
    attended = await scalar(
        session,
        select(func.count(Booking.id)).where(Booking.status == BookingStatus.ATTENDED),
    )
    no_show = await scalar(
        session,
        select(func.count(Booking.id)).where(Booking.status == BookingStatus.NO_SHOW),
    )
    clients = await scalar(session, select(func.count(ClientProfile.id)))
    referrals = await scalar(session, select(func.count(Referral.id)))
    bonus_accrued = await scalar(
        session,
        select(func.coalesce(func.sum(BonusLedger.points), 0)).where(
            BonusLedger.direction == BonusDirection.ACCRUAL
        ),
    )
    bonus_spent = await scalar(
        session,
        select(func.coalesce(func.sum(BonusLedger.points), 0)).where(
            BonusLedger.direction == BonusDirection.SPEND
        ),
    )
    revenue = await scalar(
        session,
        select(func.coalesce(func.sum(Booking.total_price), 0)).where(
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED, BookingStatus.ATTENDED])
        ),
    )
    avg_check = Decimal(revenue or 0) / confirmed if confirmed else Decimal("0")
    confirmation_conversion = (confirmed / bookings_total * 100) if bookings_total else 0
    completed_conversion = (attended / bookings_total * 100) if bookings_total else 0

    loaded_engineer = await scalar(
        session,
        select(EngineerProfile.name)
        .join(Booking)
        .group_by(EngineerProfile.id)
        .order_by(func.count(Booking.id).desc())
        .limit(1),
    )
    busiest_day = await scalar(
        session,
        select(func.date(Booking.starts_at))
        .group_by(func.date(Booking.starts_at))
        .order_by(func.count(Booking.id).desc())
        .limit(1),
    )

    return "\n".join(
        [
            "<b>Статистика</b>",
            f"Заявок: {bookings_total}",
            f"Подтверждено: {confirmed}",
            f"Ночных заявок: {night}",
            f"Состоявшихся записей: {attended}",
            f"Неявок: {no_show}",
            f"Новых клиентов: {clients}",
            f"Рефералов: {referrals}",
            f"Начислено бонусов: {bonus_accrued}",
            f"Использовано бонусов: {bonus_spent}",
            f"Выручка: {revenue}",
            f"Средний чек: {avg_check:.2f}",
            f"Конверсия подтверждения: {confirmation_conversion:.1f}%",
            f"Конверсия завершения: {completed_conversion:.1f}%",
            f"Самый загруженный день: {busiest_day or '-'}",
            f"Самый загруженный звукорежиссер: {loaded_engineer or '-'}",
        ]
    )


async def revenue_by_engineer(session: AsyncSession) -> str:
    result = await session.execute(
        select(
            EngineerProfile.name,
            func.coalesce(func.sum(Booking.total_price), 0),
            func.count(Booking.id),
            func.coalesce(func.avg(Booking.duration_hours), 0),
        )
        .join(Booking)
        .where(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED, BookingStatus.ATTENDED]))
        .group_by(EngineerProfile.id)
        .order_by(func.sum(Booking.total_price).desc())
    )
    lines = ["<b>Выручка по звукорежиссерам</b>"]
    for name, revenue, count, avg_duration in result:
        lines.append(f"{name}: {revenue} / записей: {count} / средняя длительность: {avg_duration:.1f} ч")
    return "\n".join(lines) if len(lines) > 1 else "Данных пока нет."


async def scalar(session: AsyncSession, statement):
    result = await session.execute(statement)
    return result.scalar() or 0

