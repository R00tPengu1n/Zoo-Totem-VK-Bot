import asyncio
import logging
from types import SimpleNamespace

import pytest
from vkbottle import VKAPIError

from bot import monitoring, texts
from bot.monitoring import error_hint, monitored


def test_bots_capabilities_error_has_hint():
    hint = error_hint(VKAPIError[912](error_msg="This is a chat bot feature"))

    assert hint is not None
    assert "Настройки для бота" in hint


def test_other_vk_error_has_no_hint():
    assert error_hint(VKAPIError[100](error_msg="One of the parameters is invalid")) is None


def test_regular_error_has_no_hint():
    assert error_hint(ValueError("boom")) is None


def test_unknown_vk_error_code_has_no_hint():
    assert error_hint(VKAPIError[999999](error_msg="Unknown")) is None


def test_base_vk_error_without_code_has_no_hint():
    assert error_hint(VKAPIError(error_msg="no code")) is None


# --- декоратор monitored с фейковым сообщением ---


class FakeMessage:
    from_id = 123

    def __init__(self, fail_answer: bool = False) -> None:
        self.answers: list[str] = []
        self.fail_answer = fail_answer

    async def answer(self, text: str, **kwargs) -> None:
        if self.fail_answer:
            raise ConnectionError("VK недоступен")
        self.answers.append(text)


def use_threshold(monkeypatch, threshold: float) -> None:
    # Не читаем .env: подменяем настройки только порогом медленной обработки
    monkeypatch.setattr(
        monitoring, "get_settings", lambda: SimpleNamespace(slow_handler_threshold=threshold)
    )


@pytest.fixture
def settings(monkeypatch):
    use_threshold(monkeypatch, 2.0)


def test_monitored_logs_hint_for_912_and_answers_user(settings, caplog):
    @monitored
    async def handler(message):
        raise VKAPIError[912](error_msg="This is a chat bot feature")

    message = FakeMessage()
    with caplog.at_level(logging.ERROR, logger="bot.monitoring"):
        result = asyncio.run(handler(message))

    assert result is None
    assert message.answers == [texts.ERROR]
    # Подсказка и traceback — одна запись в логе
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.exc_info is not None
    assert "Настройки для бота" in record.getMessage()
    assert "Ошибка в обработчике handler" in record.getMessage()
    assert "id123" in record.getMessage()


def test_monitored_without_hint_logs_only_traceback(settings, caplog):
    @monitored
    async def handler(message):
        raise ValueError("boom")

    message = FakeMessage()
    with caplog.at_level(logging.ERROR, logger="bot.monitoring"):
        asyncio.run(handler(message))

    assert message.answers == [texts.ERROR]
    assert len(caplog.records) == 1
    assert caplog.records[0].exc_info is not None


def test_monitored_passes_result_through_on_success(settings):
    @monitored
    async def handler(message, value):
        return value * 2

    message = FakeMessage()

    assert asyncio.run(handler(message, 21)) == 42
    assert message.answers == []


def test_monitored_survives_failed_error_answer(settings, caplog):
    @monitored
    async def handler(message):
        raise VKAPIError[912](error_msg="This is a chat bot feature")

    with caplog.at_level(logging.ERROR, logger="bot.monitoring"):
        result = asyncio.run(handler(FakeMessage(fail_answer=True)))

    assert result is None
    assert "Не удалось отправить сообщение об ошибке" in caplog.text


def test_monitored_warns_about_slow_handler(monkeypatch, caplog):
    use_threshold(monkeypatch, -1.0)

    @monitored
    async def handler(message):
        return "ok"

    with caplog.at_level(logging.WARNING, logger="bot.monitoring"):
        asyncio.run(handler(FakeMessage()))

    assert "Медленная обработка: handler" in caplog.text
