from datetime import datetime


def safe_time(value: str) -> str:
    """
    Делает время безопасным для FSM / callback data / storage
    (aiogram не любит ':' в некоторых местах)
    """
    return value.replace(":", "_")


def restore_time(value: str) -> str:
    """
    Обратное преобразование
    """
    return value.replace("_", ":")


def normalize_username(username: str | None) -> str | None:
    """
    Убирает @ и нормализует username
    """
    if not username:
        return None
    return username.lstrip("@").strip().lower()


def safe_int(value, default: int = 0) -> int:
    """
    Безопасный int парсер
    """
    try:
        return int(value)
    except Exception:
        return default


def format_full_name(first_name: str | None, last_name: str | None = None) -> str:
    """
    Красивое имя пользователя
    """
    first = first_name or ""
    last = last_name or ""
    full = f"{first} {last}".strip()
    return full if full else "Unknown"
