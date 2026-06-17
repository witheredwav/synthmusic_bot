from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.enums import BookingStatus, BookingType, ReferralStatus
from app.db.models import Booking, ClientProfile, EngineerProfile, Referral
from app.services.bonuses import reward_attended_booking
from app.services.schedule import (
    ACTIVE_STATUSES,
    has_booking_overlap,
    is_inside_work_schedule,
    localize,
    night_available,
)


class BookingError(ValueError):
    pass


async def create_booking(
    session: AsyncSession,
    client: ClientProfile,
    engineer_id: int,
    day: date,
    clock: time,
    duration_hours: int,
    client_name: str,
    client_phone: str,
    is_night: bool = False,
) -> Booking:
    engineer = await session.get(EngineerProfile, engineer_id)
    if engineer is None or not engineer.is_visible:
        raise BookingError("Звукорежиссер недоступен.")

    starts_at = localize(day, clock)
    ends_at = starts_at + timedelta(hours=duration_hours)

    if is_night:
        if not await night_available(session, engineer_id, day):
            raise BookingError("Ночная запись у этого звукорежиссера недоступна.")
        booking_type = BookingType.NIGHT
        status = BookingStatus.PENDING_MANUAL
    else:
        if duration_hours < 1 or duration_hours > 6:
            raise BookingError("Длительность должна быть от 1 до 6 часов.")
        if not await is_inside_work_schedule(session, engineer_id, starts_at, ends_at):
            raise BookingError("Выбранное время вне рабочего графика.")
        booking_type = BookingType.LONG if duration_hours >= 3 else BookingType.REGULAR
        status = BookingStatus.PENDING_MANUAL if duration_hours >= 3 else BookingStatus.PENDING_ENGINEER

    if await has_booking_overlap(session, engineer_id, starts_at, ends_at):
        raise BookingError("Это время уже занято.")

    booking = Booking(
        client_id=client.id,
        engineer_id=engineer_id,
        client=client,
        engineer=engineer,
        booking_type=booking_type,
        status=status,
        starts_at=starts_at,
        ends_at=ends_at,
        duration_hours=duration_hours,
        hourly_rate=engineer.hourly_rate,
        total_price=Decimal(duration_hours) * engineer.hourly_rate,
        client_name=client_name,
        client_phone=client_phone,
    )
    client.display_name = client_name
    client.phone = client_phone
    client.bookings_count += 1
    session.add(booking)

    referral = await session.execute(
        select(Referral).where(Referral.referred_client_id == client.id)
    )
    referral_item = referral.scalar_one_or_none()
    if referral_item and referral_item.status == ReferralStatus.REGISTERED:
        referral_item.status = ReferralStatus.BOOKED

    await session.flush()
    return booking


async def get_booking(session: AsyncSession, booking_id: int) -> Booking | None:
    return await session.get(
        Booking,
        booking_id,
        options=[
            selectinload(Booking.client).selectinload(ClientProfile.user),
            selectinload(Booking.engineer).selectinload(EngineerProfile.user),
        ],
    )


async def set_booking_status(
    session: AsyncSession,
    booking: Booking,
    status: BookingStatus,
    rejection_reason: str | None = None,
) -> Booking:
    if status in ACTIVE_STATUSES and await has_booking_overlap(
        session,
        booking.engineer_id,
        booking.starts_at,
        booking.ends_at,
    ):
        overlap = await session.execute(
            select(Booking.id).where(
                Booking.id != booking.id,
                Booking.engineer_id == booking.engineer_id,
                Booking.status.in_(ACTIVE_STATUSES),
                Booking.starts_at < booking.ends_at,
                Booking.ends_at > booking.starts_at,
            )
        )
        if overlap.scalar_one_or_none() is not None:
            raise BookingError("Время пересекается с другой записью.")

    booking.status = status
    booking.rejection_reason = rejection_reason
    if status in {BookingStatus.COMPLETED, BookingStatus.ATTENDED}:
        booking.client.completed_bookings_count += 1
    if status == BookingStatus.CANCELLED_BY_CLIENT:
        booking.client.cancelled_bookings_count += 1
    if status == BookingStatus.ATTENDED:
        booking.attended_marked_at = datetime.now(tz=booking.starts_at.tzinfo)
        await reward_attended_booking(session, booking)
    return booking
