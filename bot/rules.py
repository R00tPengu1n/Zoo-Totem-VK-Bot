"""Правила, по которым vkbottle выбирает обработчик для сообщения.

Кнопки бота отправляют служебные данные (payload) вида {"cmd": "quiz:start"}.
Правила ниже проверяют payload, а для некоторых команд — ещё и текст,
чтобы бот понимал и нажатие кнопки, и команду, набранную вручную.
"""

from collections.abc import Iterable
from typing import Any

from vkbottle.bot import Message
from vkbottle.dispatch.rules import ABCRule


def get_payload(message: Message) -> dict[str, Any]:
    """Payload сообщения в виде словаря. Если его нет или он битый — пустой словарь."""
    try:
        payload = message.get_payload_json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


class Command(ABCRule[Message]):
    """Срабатывает на кнопку с нужной командой или на один из текстов.

    Пример: Command("help", texts=["помощь", "/help"]).
    Сравнение текста не зависит от регистра и пробелов по краям.
    """

    def __init__(
        self,
        cmd: str | None = None,
        *,
        texts: Iterable[str] = (),
        payloads: Iterable[dict[str, Any]] = (),
    ) -> None:
        self.cmd = cmd
        self.texts = {text.strip().lower() for text in texts}
        self.payloads = list(payloads)

    async def check(self, event: Message) -> bool:
        payload = get_payload(event)
        if self.cmd is not None and payload.get("cmd") == self.cmd:
            return True
        if payload and payload in self.payloads:
            return True
        return (event.text or "").strip().lower() in self.texts


class AnswerButton(ABCRule[Message]):
    """Срабатывает на кнопку с вариантом ответа.

    Передаёт в обработчик номер вопроса и номер выбранного варианта.
    """

    def __init__(self, cmd: str) -> None:
        self.cmd = cmd

    async def check(self, event: Message) -> dict[str, int] | bool:
        payload = get_payload(event)
        if payload.get("cmd") != self.cmd:
            return False

        question_index = payload.get("q")
        option_index = payload.get("a")
        if not isinstance(question_index, int) or not isinstance(option_index, int):
            return False

        return {"question_index": question_index, "option_index": option_index}
