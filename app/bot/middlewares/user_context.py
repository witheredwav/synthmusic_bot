from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.db.functions import get_user


class UserContextMiddleware(BaseMiddleware):

    def __init__(self, sessionmaker: async_sessionmaker):
        self.sessionmaker = sessionmaker

    async def __call__(
        self,
        handler: Callable,
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:

        tg_user = getattr(event, "from_user", None)

        async with self.sessionmaker() as session:

            data["session"] = session

            if tg_user:
                db_user = await get_user(session, tg_user.id)
                data["db_user"] = db_user

            return await handler(event, data)
