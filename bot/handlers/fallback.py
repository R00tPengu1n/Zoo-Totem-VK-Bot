"""Сообщения, которые не подошли ни под один обработчик.

Этот модуль подключается последним.
"""

from vkbottle.bot import BotLabeler, Message

from bot import keyboards, texts
from bot.monitoring import monitored

labeler = BotLabeler()


@labeler.message()
@monitored
async def unknown_message(message: Message) -> None:
    await message.answer(texts.UNKNOWN, keyboard=keyboards.main_menu())
