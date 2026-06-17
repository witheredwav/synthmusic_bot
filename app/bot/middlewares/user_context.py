from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.services.users import get_user


class UserContextMiddleware(BaseMiddleware):
    def __init__(self, sessionmaker: async_sessionmaker):
        self.sessionmaker = sessionmaker

    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]):

        user = event.from_user

        async with self.sessionmaker() as session:

            db_user = await get_user(user.id)

            # 🔥 КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ:
            # прокидываем зависимости в handlers
            data["db_user"] = db_user
            data["session"] = session

            return await handler(event, data)
