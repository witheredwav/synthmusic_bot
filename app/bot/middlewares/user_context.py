from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.services.users import get_user


class UserContextMiddleware(BaseMiddleware):
    def __init__(self, sessionmaker: async_sessionmaker):
        self.sessionmaker = sessionmaker

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ):

        # 🔥 ПРАВИЛЬНО: достаём пользователя безопасно
        tg_user = None

        if hasattr(event, "message") and event.message:
            tg_user = event.message.from_user

        elif hasattr(event, "callback_query") and event.callback_query:
            tg_user = event.callback_query.from_user

        elif hasattr(event, "from_user"):
            tg_user = event.from_user

        if tg_user is None:
            # если вдруг update без пользователя — просто пропускаем
            return await handler(event, data)

        async with self.sessionmaker() as session:

            db_user = await get_user(tg_user.id)

            data["db_user"] = db_user
            data["session"] = session
            data["tg_user"] = tg_user

            return await handler(event, data)
