"""Проверка настроек группы VK при запуске бота.

Если в группе выключен Long Poll или не отмечены нужные события, бот либо
падает с непонятной ошибкой VK, либо молча не получает сообщения. Поэтому
перед запуском мы сами спрашиваем у VK настройки группы и, если что-то не так,
пишем в лог, где это включить.

Решение «что не так» принимает чистая функция `find_problems`: она работает
со словарями из ответа VK и легко тестируется без сети.
"""

import logging
from typing import Any

from vkbottle import API, VKAPIError

logger = logging.getLogger(__name__)

LONGPOLL_HINT = "Управление → Работа с API → Long Poll API"
EVENTS_HINT = "Управление → Работа с API → Long Poll API → Типы событий"
BOTS_HINT = "Управление → Сообщения → Настройки для бота"


# Код ошибки VK «авторизация не удалась»: ключ неверный, отозван или просрочен
INVALID_TOKEN_CODE = 5


class StartupCheckError(Exception):
    """Настройки группы VK не позволяют боту работать."""


def find_problems(
    longpoll_settings: dict[str, Any],
    group_settings: dict[str, Any] | None = None,
) -> list[str]:
    """Возвращает список проблем в настройках группы, из-за которых бот не работает.

    `longpoll_settings` — ответ groups.getLongPollSettings,
    `group_settings` — ответ groups.getSettings или None, если VK его не отдал
    (с ключом сообщества этот метод недоступен).
    """
    if not longpoll_settings.get("is_enabled"):
        return [f"В группе выключен Long Poll API. Включи его: {LONGPOLL_HINT}."]

    problems: list[str] = []
    events = longpoll_settings.get("events") or {}
    if not events.get("message_new"):
        problems.append(
            "В Long Poll API не отмечено событие «Входящее сообщение» (message_new), "
            f"бот не будет получать сообщения. Отметь его: {EVENTS_HINT}."
        )

    # Поле есть не всегда: если его нет, проверить нельзя, и это не ошибка
    if group_settings is not None and "bots_capabilities" in group_settings:
        if not group_settings["bots_capabilities"]:
            problems.append(
                "В группе выключены возможности ботов, кнопки в сообщениях "
                f"работать не будут (ошибка VK 912). Включи их: {BOTS_HINT}."
            )
    return problems


async def check_group_settings(api: API) -> None:
    """Проверяет настройки группы и пишет найденные проблемы в лог.

    Бросает StartupCheckError, если с такими настройками бот работать не сможет.
    Неверный ключ доступа тоже останавливает запуск. Если саму проверку
    выполнить не удалось по другой причине (сеть, сбой VK), только
    предупреждает: бот продолжит запуск.
    """
    try:
        response = await api.request("groups.getById", {})
        group_id = _first_group_id(response["response"])
        longpoll = await api.request("groups.getLongPollSettings", {"group_id": group_id})
    except VKAPIError as error:
        if getattr(error, "code", None) == INVALID_TOKEN_CODE:
            logger.critical("VK не принял ключ доступа сообщества: проверь VK_TOKEN в .env")
            raise StartupCheckError("Бот не может подключиться к VK") from error
        logger.warning("Не удалось проверить настройки группы VK", exc_info=True)
        return
    except Exception:
        logger.warning("Не удалось проверить настройки группы VK", exc_info=True)
        return

    try:
        settings = await api.request("groups.getSettings", {"group_id": group_id})
        group_settings = settings["response"]
    except Exception:
        logger.debug("Настройки группы недоступны, возможности ботов не проверяем")
        group_settings = None

    problems = find_problems(longpoll["response"], group_settings)
    for problem in problems:
        logger.critical(problem)
    if problems:
        raise StartupCheckError("Бот не может работать с текущими настройками группы VK")
    logger.info("Настройки группы VK id%s в порядке", group_id)


def _first_group_id(response: dict[str, Any] | list[dict[str, Any]]) -> int:
    # В новых версиях API группы лежат в поле groups, в старых — сразу списком
    groups = response["groups"] if isinstance(response, dict) else response
    return groups[0]["id"]
