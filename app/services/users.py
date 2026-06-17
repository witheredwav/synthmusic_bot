from collections.abc import Iterable

from aiogram.types import User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.enums import Role
from app.db.models import ClientProfile, EngineerProfile, Referral, User, UserRole


# =========================
# GET USER (UNIFIED API)
# =========================
async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User)
        .where(User.telegram_id == telegram_id)
        .options(selectinload(User.roles))
    )
    return result.scalar_one_or_none()


# =========================
# ENSURE USER
# =========================
async def ensure_user(
    session: AsyncSession,
    tg_user: TgUser,
    referral_code: str | None = None,
) -> User:
    user = await get_user(session, tg_user.id)
    is_new = user is None

    if user is None:
        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        session.add(user)
        await session.flush()

        session.add(UserRole(user_id=user.id, role=Role.CLIENT))
        session.add(
            ClientProfile(
                user_id=user.id,
                referral_code=str(tg_user.id),
            )
        )
        await session.flush()
    else:
        user.username = tg_user.username
        user.first_name = tg_user.first_name

    await session.refresh(user, attribute_names=["roles", "client_profile"])

    if is_new and referral_code:
        await attach_referral(session, user.client_profile, referral_code)

    return user


# =========================
# REFERRALS
# =========================
async def attach_referral(
    session: AsyncSession,
    referred_client: ClientProfile | None,
    referral_code: str,
) -> None:
    if referred_client is None:
        return

    result = await session.execute(
        select(ClientProfile).where(ClientProfile.referral_code == referral_code)
    )
    inviter = result.scalar_one_or_none()

    if inviter is None or inviter.id == referred_client.id:
        return

    exists = await session.execute(
        select(Referral).where(Referral.referred_client_id == referred_client.id)
    )
    if exists.scalar_one_or_none():
        return

    referred_client.referred_by_client_id = inviter.id
    inviter.referrals_count += 1

    session.add(
        Referral(
            inviter_client_id=inviter.id,
            referred_client_id=referred_client.id,
        )
    )


# =========================
# INITIAL ADMINS
# =========================
async def ensure_initial_admins(session: AsyncSession, telegram_ids: Iterable[int]) -> None:
    for telegram_id in telegram_ids:
        user = await get_user(session, telegram_id)

        if user is None:
            user = User(
                telegram_id=telegram_id,
                first_name="Initial admin",
            )
            session.add(user)
            await session.flush()

            session.add(
                ClientProfile(
                    user_id=user.id,
                    referral_code=str(telegram_id),
                )
            )
            await session.flush()

        await grant_role(session, user.telegram_id, Role.ADMIN)

    await session.commit()


# =========================
# GRANT ROLE (FIXED TRANSACTION)
# =========================
async def grant_role(session: AsyncSession, telegram_id: int, role: Role) -> User:
    user = await get_user(session, telegram_id)

    if user is None:
        user = User(telegram_id=telegram_id)
        session.add(user)
        await session.flush()

        session.add(
            ClientProfile(
                user_id=user.id,
                referral_code=str(telegram_id),
            )
        )

    exists = await session.execute(
        select(UserRole).where(
            UserRole.user_id == user.id,
            UserRole.role == role,
        )
    )

    if exists.scalar_one_or_none() is None:
        session.add(UserRole(user_id=user.id, role=role))

    if role == Role.ENGINEER:
        profile_exists = await session.execute(
            select(EngineerProfile).where(EngineerProfile.user_id == user.id)
        )

        if profile_exists.scalar_one_or_none() is None:
            session.add(
                EngineerProfile(
                    user_id=user.id,
                    name=user.first_name or f"Engineer {telegram_id}",
                    short_description="Profile is being configured.",
                    full_description="Profile is being configured by an administrator.",
                )
            )

    await session.flush()
    return user
