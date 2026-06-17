# app/services/users.py

"""
Temporary working user service layer
"""


def list_admin_telegram_ids():
    """Список админов (заглушка)"""
    return []


def get_user(user_id: int):
    """Получить пользователя (заглушка)"""
    return {
        "user_id": user_id,
        "username": None,
        "role": "user"
    }


def get_user_by_id(user_id: int):
    """Алиас"""
    return get_user(user_id)


def create_user(user_id: int, username: str | None = None):
    """Создание пользователя (заглушка)"""
    return {
        "user_id": user_id,
        "username": username,
        "role": "user"
    }


def grant_role(user_id: int, role: str):
    """
    Назначить роль пользователю
    (заглушка, чтобы бот не падал)
    """

    # TODO: подключить БД и реально сохранять роль

    return {
        "user_id": user_id,
        "role": role,
        "status": "granted"
    }
