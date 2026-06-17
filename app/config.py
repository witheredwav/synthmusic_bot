from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    bot_username: str = Field(default="BOT_USERNAME", alias="BOT_USERNAME")
    database_url: str = Field(alias="DATABASE_URL")
    initial_admin_ids: str = Field(default="", alias="INITIAL_ADMIN_IDS")
    timezone: str = Field(default="Asia/Yekaterinburg", alias="TIMEZONE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    studio_name: str = Field(default="Recording Studio", alias="STUDIO_NAME")
    studio_contacts: str = Field(default="Contacts are not configured.", alias="STUDIO_CONTACTS")
    booking_start_hour: int = Field(default=11, alias="BOOKING_START_HOUR")
    booking_end_hour: int = Field(default=22, alias="BOOKING_END_HOUR")
    slot_step_minutes: int = Field(default=30, alias="SLOT_STEP_MINUTES")
    reminder_client_hours: str = Field(default="24,2", alias="REMINDER_CLIENT_HOURS")

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url

    @property
    def admin_ids(self) -> set[int]:
        return {int(item.strip()) for item in self.initial_admin_ids.split(",") if item.strip()}

    @property
    def reminder_hours(self) -> list[int]:
        return [int(item.strip()) for item in self.reminder_client_hours.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
