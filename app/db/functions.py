from sqlalchemy import select
from app.db.models import User
from app.db.session import async_session_factory


async def get_or_create_user(user_id: int, username: str | None = None) -> User:
    async with async_session_factory() as session:

        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            return user

        # 🔥 если нет — создаём
        user = User(
            id=user_id,
            username=username,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        return user
