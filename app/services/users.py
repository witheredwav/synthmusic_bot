# app/services/users.py

"""
Temporary working user service layer (FIXED SIGNATURES)
"""


def list_admin_telegram_ids():
    return []


def get_user(user_id: int):
    return {
        "user_id": user_id,
        "username": None,
        "role": "user"
    }


def get_user_by_id(user_id: int):
    return get_user(user_id)


def create_user(user_id: int, username: str | None = None):
    return {
        "user_id": user_id,
        "username": username,
        "role": "user"
    }


def grant_role(user_id: int, role: str):
    return {
        "user_id": user_id,
        "role": role,
        "status": "granted"
    }


# 🔥 ВАЖНО: теперь функция принимает 2 аргумента как в main.py
async def ensure_initial_admins(session, admin_ids):
    """
    Инициализация админов при старте
    session -> SQLAlchemy session (пока не используем)
    admin_ids -> список админов из settings
    """

    # TODO: здесь должна быть логика записи админов в БД

    return {
        "status": "ok",
        "admins_received": admin_ids,
        "initialized": True
    }
