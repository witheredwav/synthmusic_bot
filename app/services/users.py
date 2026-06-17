# app/services/users.py

"""
User service layer (temporary working version)
"""


def list_admin_telegram_ids():
    """
    Список админов Telegram
    (заглушка)
    """
    return []


def get_user(user_id: int):
    """
    Получить пользователя по ID
    (заглушка, чтобы middleware не падал)
    """

    return {
        "user_id": user_id,
        "username": None
    }


def get_user_by_id(user_id: int):
    """
    Альтернативное имя функции (на случай старых импортов)
    """

    return get_user(user_id)


def create_user(user_id: int, username: str | None = None):
    """
    Создание пользователя (заглушка)
    """

    return {
        "user_id": user_id,
        "username": username
    }
