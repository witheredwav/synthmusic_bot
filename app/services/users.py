# app/services/users.py

"""
User service layer
"""

def list_admin_telegram_ids():
    """
    Возвращает список Telegram ID админов.
    Сейчас это заглушка, чтобы бот запускался без ошибок.
    """

    # TODO: заменить на реальную логику (БД / конфиг / env)

    return []


def get_user_by_id(user_id: int):
    """
    Заглушка под пользователя (если где-то используется)
    """

    return None


def create_user(user_id: int, username: str | None = None):
    """
    Заглушка создания пользователя
    """

    return {
        "user_id": user_id,
        "username": username
    }
