from aiogram import BaseMiddleware
from app.services.users import get_user


class UserContextMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):

        # Telegram Update → безопасно достаём пользователя
        tg_user = None

        if hasattr(event, "from_user") and event.from_user:
            tg_user = event.from_user
        elif hasattr(event, "message") and event.message:
            tg_user = event.message.from_user
        elif hasattr(event, "callback_query") and event.callback_query:
            tg_user = event.callback_query.from_user

        if not tg_user:
            return await handler(event, data)

        # получаем пользователя (sync в твоей версии)
        db_user = get_user(tg_user.id)

        data["db_user"] = db_user
        data["tg_user"] = tg_user

        return await handler(event, data)
