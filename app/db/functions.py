from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


# =========================
# 👤 GET USER
# =========================
async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User)
        .options(selectinload(User.roles))  # 🔥 чтобы не было DetachedInstanceError
        .where(User.telegram_id == telegram_id)
    )

    return result.scalar_one_or_none()


# =========================
# 👤 CREATE USER
# =========================
async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
) -> User:

    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        is_active=True
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


# =========================
# 👤 GET OR CREATE USER
# =========================
async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
) -> User:

    user = await get_user(session, telegram_id)

    if user:
        return user

    return await create_user(
        session=session,
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
    )
