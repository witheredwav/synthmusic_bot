class DBUser:
    def __init__(self, user_id: int, username: str | None = None, role: str = "user"):
        self.user_id = user_id
        self.username = username
        self.role = role

    def has_role(self, role: str) -> bool:
        return self.role == role


def list_admin_telegram_ids():
    return []


def get_user(user_id: int):
    # теперь возвращаем объект, НЕ dict
    return DBUser(user_id=user_id, role="user")


def get_user_by_id(user_id: int):
    return get_user(user_id)


def create_user(user_id: int, username: str | None = None):
    return DBUser(user_id=user_id, username=username, role="user")


def grant_role(user_id: int, role: str):
    return DBUser(user_id=user_id, role=role)


async def ensure_initial_admins(session, admin_ids):
    return {
        "status": "ok",
        "admins": admin_ids
    }
