from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


async def get_user(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.telegram_id == telegram_id)
    )

    return result.scalar_one_or_none()
