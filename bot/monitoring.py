"""Мониторинг обработчиков: время выполнения и ошибки.

Декоратор `monitored` оборачивает каждый обработчик:
- замеряет, сколько заняла обработка сообщения, и предупреждает в логе,
  если дольше порога из настроек;
- ловит любые ошибки, пишет их в лог с полным traceback и отвечает
  пользователю, что что-то пошло не так, вместо того чтобы молчать.
"""

import functools
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from vkbottle.bot import Message

from bot import texts
from bot.config import get_settings

logger = logging.getLogger("bot.monitoring")

Handler = Callable[..., Awaitable[Any]]


def monitored(handler: Handler) -> Handler:
    @functools.wraps(handler)
    async def wrapper(message: Message, *args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        try:
            return await handler(message, *args, **kwargs)
        except Exception:
            logger.exception(
                "Ошибка в обработчике %s (пользователь id%s)",
                handler.__name__,
                message.from_id,
            )
            try:
                await message.answer(texts.ERROR)
            except Exception:
                logger.exception("Не удалось отправить сообщение об ошибке")
            return None
        finally:
            elapsed = time.perf_counter() - started
            threshold = get_settings().slow_handler_threshold
            if elapsed > threshold:
                logger.warning(
                    "Медленная обработка: %s заняла %.2f с (порог %.2f с)",
                    handler.__name__,
                    elapsed,
                    threshold,
                )
            else:
                logger.debug("%s обработан за %.3f с", handler.__name__, elapsed)

    return wrapper
