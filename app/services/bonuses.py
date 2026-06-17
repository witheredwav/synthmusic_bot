from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.enums import (
    BookingStatus,
    BonusDirection,
    BonusReason,
    ReferralStatus,
)
from app.db.models import BonusLedger, Booking, ClientProfile, Referral


VISIT_POINTS = 2
REFERRAL_POINTS = 2
REWARD_10_COST = 10
REWARD_20_COST = 20


async def accrue_points(
    session: AsyncSession,
    client: ClientProfile,
    points: int,
    reason: BonusReason,
    booking_id: int | None = None,
    comment: str | None = None,
) -> None:
    client.bonus_points += points
    session.add(
        BonusLedger(
            client_id=client.id,
            booking_id=booking_id,
            direction=BonusDirection.ACCRUAL,
            reason=reason,
            points=points,
            comment=comment,
        )
    )


async def spend_points(
    session: AsyncSession,
    client: ClientProfile,
    points: int,
    reason: BonusReason,
    comment: str | None = None,
) -> bool:
    if client.bonus_points < points:
        return False
    client.bonus_points -= points
    session.add(
        BonusLedger(
            client_id=client.id,
            direction=BonusDirection.SPEND,
            reason=reason,
            points=points,
            comment=comment,
        )
    )
    return True


async def reward_attended_booking(session: AsyncSession, booking: Booking) -> None:
    if booking.status != BookingStatus.ATTENDED:
        return

    existing_visit = await session.execute(
        select(BonusLedger).where(
            BonusLedger.booking_id == booking.id,
            BonusLedger.reason == BonusReason.VISIT,
        )
    )
    if existing_visit.scalar_one_or_none() is None:
        await accrue_points(
            session,
            booking.client,
            VISIT_POINTS,
            BonusReason.VISIT,
            booking_id=booking.id,
            comment="Visit confirmed",
        )

    referral_result = await session.execute(
        select(Referral).where(
            Referral.referred_client_id == booking.client_id,
            Referral.status != ReferralStatus.REWARDED,
        )
    )
    referral = referral_result.scalar_one_or_none()
    if referral is None:
        return

    inviter = await session.get(ClientProfile, referral.inviter_client_id)
    if inviter is None:
        return
    await accrue_points(
        session,
        inviter,
        REFERRAL_POINTS,
        BonusReason.REFERRAL,
        booking_id=booking.id,
        comment=f"Referral visit by client #{booking.client_id}",
    )
    referral.status = ReferralStatus.REWARDED
    referral.rewarded_at = datetime.now(tz=booking.starts_at.tzinfo)

