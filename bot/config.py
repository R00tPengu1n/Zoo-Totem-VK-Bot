"""Настройки приложения, загружаемые из переменных окружения и файла .env."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    vk_token: SecretStr = Field(description="Ключ доступа сообщества VK")
    admin_vk_id: str = Field(
        description="ID или короткое имя сотрудника, которому бот пересылает вопросы",
    )
    bot_link: str = Field(
        description="Публичная ссылка на диалог с ботом, например https://vk.me/club123",
    )
    guardianship_url: str = "https://moscowzoo.ru/my-zoo/become-a-guardian/"
    contact_email: str = Field(
        default="zoofriends@moscowzoo.ru",
        description="Почта для связи, если переслать вопрос сотруднику не удалось",
    )

    database_url: str = f"sqlite+aiosqlite:///{(BASE_DIR / 'storage' / 'bot.db').as_posix()}"

    data_dir: Path = BASE_DIR / "data"
    log_dir: Path = BASE_DIR / "logs"
    log_level: str = "INFO"
    slow_handler_threshold: float = Field(
        default=2.0,
        description="Через сколько секунд обработка сообщения считается медленной",
    )

    @property
    def questions_path(self) -> Path:
        return self.data_dir / "questions.json"

    @property
    def animals_path(self) -> Path:
        return self.data_dir / "animals.json"

    @property
    def images_dir(self) -> Path:
        return self.data_dir / "images"


@lru_cache
def get_settings() -> Settings:
    return Settings()
