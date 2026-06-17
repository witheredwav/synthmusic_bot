from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.models import User
from app.services.users import get_user


class UserContextMiddleware(BaseMiddleware):
    def __init__(self, sessionmaker: async_sessionmaker):
        self.sessionmaker = sessionmaker

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ):
        tg_user = getattr(event, "from_user", None)

        if not tg_user:
            return await handler(event, data)

        async with self.sessionmaker() as session:
            db_user: User | None = await get_user(session, tg_user.id)

            data["db_user"] = db_user
            data["session"] = session  # 👈 ВАЖНО

            return await handler(event, data)
