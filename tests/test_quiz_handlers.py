import asyncio
from types import SimpleNamespace

import pytest
from vkbottle import BuiltinStateDispenser

from bot import monitoring
from bot.handlers import quiz
from bot.states import DialogState


class SlowStateDispenser(BuiltinStateDispenser):
    """Хранилище состояний, которое отвечает не мгновенно, как Redis или БД.

    Встроенное хранилище vkbottle работает без пауз, и гонка на нём
    не воспроизводится. Здесь после чтения управление отдаётся другим задачам.
    """

    def __init__(self) -> None:
        super().__init__()
        self.writes = 0

    async def get(self, peer_id: int):
        state = await super().get(peer_id)
        await asyncio.sleep(0)
        return state

    async def set(self, peer_id: int, state, **payload) -> None:
        self.writes += 1
        await super().set(peer_id, state, **payload)


class FakeRepository:
    def __init__(self) -> None:
        self.saved: list[tuple[int, str]] = []

    async def save_result(self, user_id: int, animal_id: str) -> None:
        self.saved.append((user_id, animal_id))


class FakePhotoService:
    async def get_attachment(self, animal, peer_id: int) -> None:
        return None


class FakeMessage:
    peer_id = 42
    from_id = 42

    def __init__(self) -> None:
        self.answers: list[str] = []

    async def answer(self, text: str, **kwargs) -> None:
        await asyncio.sleep(0)
        self.answers.append(text)


@pytest.fixture
def env(monkeypatch):
    dispenser = SlowStateDispenser()
    repository = FakeRepository()
    monkeypatch.setattr(quiz, "state_dispenser", dispenser)
    monkeypatch.setattr(quiz, "repository", repository)
    monkeypatch.setattr(quiz, "photo_service", FakePhotoService())
    monkeypatch.setattr(
        monitoring, "get_settings", lambda: SimpleNamespace(slow_handler_threshold=60)
    )
    return SimpleNamespace(dispenser=dispenser, repository=repository)


async def double_tap(question_index: int) -> None:
    await asyncio.gather(
        quiz.handle_answer(FakeMessage(), question_index=question_index, option_index=0),
        quiz.handle_answer(FakeMessage(), question_index=question_index, option_index=0),
    )


def test_double_tap_advances_quiz_once(env):
    async def scenario():
        await env.dispenser.set(42, DialogState.ANSWERING, question_index=0, scores={})
        env.dispenser.writes = 0
        await double_tap(0)
        return await env.dispenser.get(42)

    state = asyncio.run(scenario())

    assert state.payload["question_index"] == 1
    assert env.dispenser.writes == 1


def test_double_tap_on_last_question_saves_result_once(env):
    last = len(quiz.content.questions) - 1

    async def scenario():
        await env.dispenser.set(42, DialogState.ANSWERING, question_index=last, scores={})
        await double_tap(last)

    asyncio.run(scenario())

    assert len(env.repository.saved) == 1
