from typing import Optional


class DBUser:
    """
    Унифицированный объект пользователя, который заменяет ORM/DICT
    """

    def __init__(
        self,
        user_id: int,
        username: Optional[str] = None,
        role: str = "user",
    ):
        # важно: проект использует И id И user_id → даём оба
        self.id = user_id
        self.user_id = user_id
        self.username = username
        self.role = role

    def has_role(self, role: str) -> bool:
        return self.role == role


# -------------------------
# MOCK / TEMP IMPLEMENTATION
# (чтобы бот не падал)
# -------------------------

def get_user(user_id: int) -> DBUser:
    return DBUser(user_id=user_id, role="user")


def grant_role(user_id: int, role: str) -> DBUser:
    return DBUser(user_id=user_id, role=role)


def list_admin_telegram_ids():
    return []


async def ensure_initial_admins(session, admin_ids):
    # временно заглушка
    return {
        "status": "ok",
        "admins": admin_ids,
    }
