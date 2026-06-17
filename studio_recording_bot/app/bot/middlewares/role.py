from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.services.users import ensure_user


class UserContextMiddleware(BaseMiddleware):
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = None
        referral_code = None
        if isinstance(event, Message):
            tg_user = event.from_user
            if event.text and event.text.startswith("/start ref_"):
                referral_code = event.text.split("ref_", 1)[1].strip()
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user

        async with self.session_factory() as session:
            if tg_user is not None:
                data["db_user"] = await ensure_user(session, tg_user, referral_code)
                await session.commit()
            data["session"] = session
            return await handler(event, data)

