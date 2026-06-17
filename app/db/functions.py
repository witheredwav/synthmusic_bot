from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import User
from app.db.session import async_session_factory


async def get_user(user_id: int) -> User | None:
    async with async_session_factory() as session:

        result = await session.execute(
            select(User)
            .options(selectinload(User.roles))  # 🔥 ВАЖНО
            .where(User.telegram_id == user_id)
        )

        return result.scalar_one_or_none()
