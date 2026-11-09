import asyncio
import logging

import pytest
from vkbottle import VKAPIError

from bot.services.startup_checks import StartupCheckError, check_group_settings, find_problems

LONGPOLL_OK = {"is_enabled": True, "api_version": "5.199", "events": {"message_new": 1}}


def test_good_settings_have_no_problems():
    assert find_problems(LONGPOLL_OK, {"bots_capabilities": 1}) == []


def test_disabled_longpoll_is_reported():
    problems = find_problems({"is_enabled": False, "events": {"message_new": 1}})

    assert len(problems) == 1
    assert "Long Poll API" in problems[0]
    assert "Управление → Работа с API" in problems[0]


def test_missing_message_new_event_is_reported():
    problems = find_problems({"is_enabled": True, "events": {"message_new": 0}})

    assert len(problems) == 1
    assert "message_new" in problems[0]


def test_missing_events_field_is_reported():
    problems = find_problems({"is_enabled": True})

    assert len(problems) == 1
    assert "message_new" in problems[0]


def test_disabled_bots_capabilities_is_reported():
    problems = find_problems(LONGPOLL_OK, {"bots_capabilities": 0})

    assert len(problems) == 1
    assert "Настройки для бота" in problems[0]


def test_unknown_bots_capabilities_is_not_a_problem():
    assert find_problems(LONGPOLL_OK, None) == []
    assert find_problems(LONGPOLL_OK, {"title": "Группа"}) == []


def test_all_problems_are_reported_together():
    problems = find_problems(
        {"is_enabled": True, "events": {"message_new": 0}},
        {"bots_capabilities": 0},
    )

    assert len(problems) == 2


def test_longpoll_enabled_as_zero_is_reported():
    # VK отдаёт флаги числами: 0 означает «выключено»
    problems = find_problems({"is_enabled": 0, "events": {"message_new": 1}})

    assert len(problems) == 1
    assert "Long Poll API" in problems[0]


def test_disabled_longpoll_hides_other_problems():
    problems = find_problems({"is_enabled": False}, {"bots_capabilities": 0})

    assert len(problems) == 1


def test_events_null_is_reported():
    problems = find_problems({"is_enabled": True, "events": None})

    assert len(problems) == 1
    assert "message_new" in problems[0]


# --- check_group_settings с подменённым API ---


class FakeAPI:
    """Подменяет api.request: ответ или ошибка задаются по имени метода."""

    def __init__(self, responses: dict) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict]] = []

    async def request(self, method: str, params: dict) -> dict:
        self.calls.append((method, params))
        result = self.responses[method]
        if isinstance(result, BaseException):
            raise result
        return {"response": result}


def make_api(**overrides) -> FakeAPI:
    responses = {
        "groups.getById": {"groups": [{"id": 42, "name": "Зоопарк"}]},
        "groups.getLongPollSettings": LONGPOLL_OK,
        "groups.getSettings": {"bots_capabilities": 1},
    }
    responses.update({key.replace("_", "."): value for key, value in overrides.items()})
    return FakeAPI(responses)


def test_check_passes_with_dict_response_from_get_by_id(caplog):
    api = make_api()

    with caplog.at_level(logging.INFO, logger="bot.services.startup_checks"):
        asyncio.run(check_group_settings(api))

    assert ("groups.getLongPollSettings", {"group_id": 42}) in api.calls
    assert ("groups.getSettings", {"group_id": 42}) in api.calls
    assert "id42 в порядке" in caplog.text


def test_check_passes_with_list_response_from_get_by_id():
    api = make_api(groups_getById=[{"id": 7}])

    asyncio.run(check_group_settings(api))

    assert ("groups.getLongPollSettings", {"group_id": 7}) in api.calls


def test_network_error_on_get_by_id_only_warns(caplog):
    api = make_api(groups_getById=TimeoutError())

    with caplog.at_level(logging.WARNING):
        asyncio.run(check_group_settings(api))

    assert [r.levelno for r in caplog.records] == [logging.WARNING]
    assert len(api.calls) == 1


def test_network_error_on_longpoll_settings_only_warns(caplog):
    api = make_api(groups_getLongPollSettings=OSError("connection reset"))

    with caplog.at_level(logging.WARNING):
        asyncio.run(check_group_settings(api))

    assert [r.levelno for r in caplog.records] == [logging.WARNING]
    assert "Не удалось проверить" in caplog.text
    assert all(method != "groups.getSettings" for method, _ in api.calls)


def test_empty_get_by_id_response_only_warns(caplog):
    api = make_api(groups_getById={"groups": []})

    with caplog.at_level(logging.WARNING):
        asyncio.run(check_group_settings(api))

    assert [r.levelno for r in caplog.records] == [logging.WARNING]


def test_get_settings_failure_still_checks_longpoll(caplog):
    api = make_api(
        groups_getLongPollSettings={"is_enabled": False},
        groups_getSettings=VKAPIError[27](error_msg="Group authorization failed"),
    )

    with caplog.at_level(logging.CRITICAL), pytest.raises(StartupCheckError):
        asyncio.run(check_group_settings(api))

    assert "выключен Long Poll API" in caplog.text


def test_get_settings_failure_with_good_longpoll_passes():
    api = make_api(groups_getSettings=VKAPIError[27](error_msg="Group authorization failed"))

    asyncio.run(check_group_settings(api))


def test_every_problem_is_logged_as_critical_before_raising(caplog):
    api = make_api(
        groups_getLongPollSettings={"is_enabled": True, "events": {"message_new": 0}},
        groups_getSettings={"bots_capabilities": 0},
    )

    with caplog.at_level(logging.CRITICAL), pytest.raises(StartupCheckError):
        asyncio.run(check_group_settings(api))

    critical = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert len(critical) == 2


def test_disabled_bots_capabilities_raises():
    api = make_api(groups_getSettings={"bots_capabilities": 0})

    with pytest.raises(StartupCheckError):
        asyncio.run(check_group_settings(api))


@pytest.mark.parametrize("method", ["groups_getById", "groups_getLongPollSettings"])
def test_invalid_token_stops_startup_with_hint(method, caplog):
    api = make_api(**{method: VKAPIError[5](error_msg="User authorization failed")})

    with caplog.at_level(logging.CRITICAL), pytest.raises(StartupCheckError):
        asyncio.run(check_group_settings(api))

    assert "VK_TOKEN" in caplog.text


def test_other_vk_error_on_get_by_id_only_warns(caplog):
    api = make_api(groups_getById=VKAPIError[10](error_msg="Internal server error"))

    with caplog.at_level(logging.WARNING):
        asyncio.run(check_group_settings(api))

    assert [r.levelno for r in caplog.records] == [logging.WARNING]
