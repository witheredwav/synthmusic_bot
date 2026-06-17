class UserContextMiddleware(BaseMiddleware):

    def __init__(self, sessionmaker: async_sessionmaker):
        self.sessionmaker = sessionmaker

    async def __call__(
        self,
        handler,
        event,
        data,
    ):
        tg_user = getattr(event, "from_user", None)

        if not tg_user:
            return await handler(event, data)

        async with self.sessionmaker() as session:
            db_user = await get_user(session, tg_user.id)
            data["db_user"] = db_user

            return await handler(event, data)
