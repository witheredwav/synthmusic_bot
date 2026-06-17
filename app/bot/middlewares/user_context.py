from aiogram import BaseMiddleware
from typing import Callable, Awaitable, Dict, Any

from app.services.users import get_user


class UserContextMiddleware(BaseMiddleware):

    def __init__(self, session_factory=None):
        super().__init__()
        self.session_factory = session_factory

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any],
    ):

        tg_user = None

        if hasattr(event, "from_user") and event.from_user:
            tg_user = event.from_user
        elif hasattr(event, "message") and event.message:
            tg_user = event.message.from_user
        elif hasattr(event, "callback_query") and event.callback_query:
            tg_user = event.callback_query.from_user

        if not tg_user:
            return await handler(event, data)

        # user
        db_user = get_user(tg_user.id)

        # 🔥 ВАЖНО: создаём session (заглушка если нет DB)
        session = self.session_factory() if self.session_factory else None

        data["tg_user"] = tg_user
        data["db_user"] = db_user
        data["session"] = session

        return await handler(event, data)
