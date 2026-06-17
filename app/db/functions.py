from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import User
from app.db.session import async_session_factory


async def get_user(user_id: int) -> User | None:
    async with async_session_factory() as session:

        result = await session.execute(
            select(User)
            .options(selectinload(User.roles))
            .where(User.telegram_id == user_id)
        )

        return result.scalar_one_or_none()


async def create_user(user_id: int, username: str | None) -> User:
    async with async_session_factory() as session:

        user = User(
            telegram_id=user_id,
            username=username,
            is_active=True
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user
