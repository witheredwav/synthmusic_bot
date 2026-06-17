# app/services/users.py

"""
Temporary working user service layer (FIX VERSION)
"""


def list_admin_telegram_ids():
    """Список админов"""
    return []


def get_user(user_id: int):
    """Получить пользователя"""
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


def ensure_initial_admins():
    """
    Создание начальных админов при старте проекта
    (заглушка, чтобы бот не падал)
    """

    # TODO: здесь обычно:
    # - читают .env
    # - или создают первого админа в БД

    return {
        "status": "ok",
        "admins_initialized": True
    }
