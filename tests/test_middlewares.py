import asyncio
from types import SimpleNamespace

import pytest

from bot.middlewares import PrivateMessagesOnly, is_private_chat

# VK выдаёт новым пользователям id больше 2 000 000 000,
# поэтому отличать беседу по величине peer_id нельзя
BIG_USER_ID = 200_000_000_123


@pytest.mark.parametrize(
    ("peer_id", "from_id", "expected"),
    [
        (1, 1, True),
        (123456789, 123456789, True),
        (BIG_USER_ID, BIG_USER_ID, True),
        (2_000_000_001, 123, False),
        (2_000_000_001, BIG_USER_ID, False),
    ],
)
def test_is_private_chat(peer_id, from_id, expected):
    assert is_private_chat(peer_id, from_id) is expected


def run_middleware(peer_id: int, from_id: int) -> PrivateMessagesOnly:
    middleware = PrivateMessagesOnly(SimpleNamespace(peer_id=peer_id, from_id=from_id))
    asyncio.run(middleware.pre())
    return middleware


def test_private_message_is_processed():
    assert run_middleware(42, 42).can_forward


def test_private_message_from_user_with_big_id_is_processed():
    # Регрессия: такие сообщения раньше молча отбрасывались как сообщения из беседы
    assert run_middleware(BIG_USER_ID, BIG_USER_ID).can_forward


def test_group_chat_message_is_ignored():
    assert not run_middleware(2_000_000_001, 123).can_forward
