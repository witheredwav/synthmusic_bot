from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.enums import BookingStatus
from app.db.models import Booking, DayOff, EngineerProfile, WorkInterval

ACTIVE_STATUSES = {
    BookingStatus.PENDING_ENGINEER,
    BookingStatus.PENDING_MANUAL,
    BookingStatus.CONFIRMED,
}


def localize(day: date, clock: time) -> datetime:
    tz = ZoneInfo(get_settings().timezone)
    return datetime.combine(day, clock, tzinfo=tz)


def slot_range(day: date) -> list[time]:
    settings = get_settings()
    cursor = datetime.combine(day, time(settings.booking_start_hour, 0))
    end = datetime.combine(day, time(settings.booking_end_hour, 0))
    slots: list[time] = []
    while cursor <= end:
        slots.append(cursor.time())
        cursor += timedelta(minutes=settings.slot_step_minutes)
    return slots


async def is_inside_work_schedule(
    session: AsyncSession,
    engineer_id: int,
    starts_at: datetime,
    ends_at: datetime,
) -> bool:
    day = starts_at.date()
    day_off = await session.execute(
        select(DayOff).where(DayOff.engineer_id == engineer_id, DayOff.day == day)
    )
    if day_off.scalar_one_or_none() is not None:
        return False

    result = await session.execute(
        select(WorkInterval).where(
            WorkInterval.engineer_id == engineer_id,
            WorkInterval.weekday == starts_at.weekday(),
            WorkInterval.is_active.is_(True),
            WorkInterval.start_time <= starts_at.timetz().replace(tzinfo=None),
            WorkInterval.end_time >= ends_at.timetz().replace(tzinfo=None),
        )
    )
    intervals = result.scalars().all()
    if intervals:
        return True

    # If no explicit schedule exists yet, allow the studio default interval.
    any_schedule = await session.execute(
        select(exists().where(WorkInterval.engineer_id == engineer_id))
    )
    if not any_schedule.scalar():
        settings = get_settings()
        return (
            starts_at.time() >= time(settings.booking_start_hour, 0)
            and ends_at.time() <= time(settings.booking_end_hour, 0)
        )
    return False


async def has_booking_overlap(
    session: AsyncSession,
    engineer_id: int,
    starts_at: datetime,
    ends_at: datetime,
) -> bool:
    result = await session.execute(
        select(exists().where(
            and_(
                Booking.engineer_id == engineer_id,
                Booking.status.in_(ACTIVE_STATUSES),
                Booking.starts_at < ends_at,
                Booking.ends_at > starts_at,
            )
        ))
    )
    return bool(result.scalar())


async def available_slots(
    session: AsyncSession,
    engineer: EngineerProfile,
    day: date,
    duration_hours: int = 1,
) -> list[time]:
    result: list[time] = []
    for clock in slot_range(day):
        starts_at = localize(day, clock)
        ends_at = starts_at + timedelta(hours=duration_hours)
        if await is_inside_work_schedule(session, engineer.id, starts_at, ends_at):
            if not await has_booking_overlap(session, engineer.id, starts_at, ends_at):
                result.append(clock)
    return result


async def active_engineers(session: AsyncSession) -> list[EngineerProfile]:
    result = await session.execute(
        select(EngineerProfile).where(EngineerProfile.is_visible.is_(True)).order_by(EngineerProfile.name)
    )
    return list(result.scalars())

async def night_available(session: AsyncSession, engineer_id: int, day: date) -> bool:
    engineer = await session.get(EngineerProfile, engineer_id)
    if engineer is None or not engineer.accepts_night_requests:
        return False
    result = await session.execute(
        select(DayOff).where(
            or_(
                DayOff.engineer_id == engineer_id,
                DayOff.engineer_id.is_(None),
            ),
            DayOff.day == day,
            DayOff.night_disabled.is_(True),
        )
    )
    return result.scalar_one_or_none() is None

