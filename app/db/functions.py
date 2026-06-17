from sqlalchemy import select
from app.db.models import User
from app.db.session import async_session  # ⚠️ если у тебя другое имя — скажешь


async def get_user(user_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
