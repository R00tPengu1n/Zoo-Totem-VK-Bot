"""Настройка логирования: в консоль и в файл с ротацией."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_FILE_MAX_BYTES = 5 * 1024 * 1024
LOG_FILE_BACKUPS = 5


def setup_logging(log_dir: Path | None = None, level: str = "INFO") -> None:
    """Логи пишутся в консоль, а если указан каталог — ещё и в файл.

    Файл ротируется: при достижении 5 МБ создаётся новый, а хранится
    не больше пяти старых. Так логи не займут весь диск.
    """
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(
            RotatingFileHandler(
                log_dir / "bot.log",
                maxBytes=LOG_FILE_MAX_BYTES,
                backupCount=LOG_FILE_BACKUPS,
                encoding="utf-8",
            )
        )

    logging.basicConfig(
        level=level.upper(),
        format=LOG_FORMAT,
        handlers=handlers,
        force=True,
    )
    # Подробные логи библиотек нужны редко — оставляем только важное
    logging.getLogger("vkbottle").setLevel(logging.INFO)
    logging.getLogger("aiosqlite").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
