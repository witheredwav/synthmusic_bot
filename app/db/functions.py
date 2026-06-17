from sqlalchemy import select

from app.db.models import User
from app.db.session import async_session_factory


async def get_or_create_user(user_id: int, username: str | None) -> User:
    async with async_session_factory() as session:

        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        # 🔥 СОЗДАНИЕ ПОЛЬЗОВАТЕЛЯ
        user = User(
            telegram_id=user_id,   # ❗ ВОТ ЭТО ОБЯЗАТЕЛЬНО
            username=username,
            is_active=True
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user
