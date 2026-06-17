from datetime import date, time

def test_default_slot_range(monkeypatch):
    monkeypatch.setenv("BOT_TOKEN", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/db")

    from app.config import get_settings
    from app.services.schedule import slot_range

    get_settings.cache_clear()
    slots = slot_range(date(2026, 6, 17))
    assert slots[0] == time(11, 0)
    assert slots[-1] == time(22, 0)
    assert time(11, 30) in slots
