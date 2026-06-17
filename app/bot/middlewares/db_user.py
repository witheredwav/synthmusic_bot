from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.db.functions import get_user


class DBUserMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        user_id = None

        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id

        if user_id:
            db_user = await get_user(user_id)
            data["db_user"] = db_user

        return await handler(event, data)
