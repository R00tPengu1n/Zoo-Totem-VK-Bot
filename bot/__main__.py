"""Точка входа. Запуск: python -m bot"""

import asyncio
import logging
import sys

from pydantic import ValidationError

from bot.logging_config import setup_logging
from bot.services.content import ContentError

logger = logging.getLogger("bot")


async def run() -> None:
    # Импорты внутри функции: модуль loader читает .env и JSON-файлы,
    # и если там ошибка, мы хотим красиво сообщить о ней в лог.
    from vkbottle import Bot

    from bot import loader
    from bot.db.session import init_db
    from bot.handlers import labelers

    setup_logging(loader.settings.log_dir, loader.settings.log_level)

    await init_db(loader.engine)
    await loader.notifier.resolve_admin()

    bot = Bot(api=loader.api, state_dispenser=loader.state_dispenser)
    for labeler in labelers:
        bot.labeler.load(labeler)

    logger.info(
        "Бот запущен: %d вопросов, %d животных",
        len(loader.content.questions),
        len(loader.content.animals),
    )
    try:
        await bot.run_polling()
    finally:
        await loader.engine.dispose()


def main() -> int:
    setup_logging()
    try:
        asyncio.run(run())
    except ValidationError as error:
        logger.critical("Ошибка в настройках. Проверь файл .env:\n%s", error)
        return 1
    except ContentError as error:
        logger.critical("Ошибка в контенте викторины: %s", error)
        return 1
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    return 0


if __name__ == "__main__":
    sys.exit(main())
