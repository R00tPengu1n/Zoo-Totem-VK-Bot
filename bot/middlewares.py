"""Промежуточные обработчики (middleware): срабатывают до выбора обработчика.

Бот работает только в личных сообщениях. В беседах у всех участников общий
peer_id, а состояние викторины хранится по peer_id, поэтому ответы разных
людей смешались бы. Сообщения из бесед бот просто игнорирует.
"""

from vkbottle import BaseMiddleware
from vkbottle.bot import Message


def is_private_chat(peer_id: int, from_id: int) -> bool:
    """Личный диалог: сообщение пришло из диалога с самим отправителем.

    В беседе peer_id — id беседы, и он не совпадает с id отправителя.
    Сравнивать peer_id с порогом 2 000 000 000 нельзя: VK уже выдаёт
    пользователям id больше этого числа.
    """
    return peer_id == from_id


class PrivateMessagesOnly(BaseMiddleware[Message]):
    async def pre(self) -> None:
        if not is_private_chat(self.event.peer_id, self.event.from_id):
            self.stop("Сообщение из беседы, бот работает только в личных сообщениях")
