"""Общие команды: начало, меню, помощь, отмена, статистика.

Эти обработчики подключаются первыми и работают в любом состоянии:
например, «Отмена» или «Меню» выведут пользователя даже из середины викторины.
"""

from vkbottle.bot import BotLabeler, Message

from bot import keyboards, texts
from bot.keyboards import VK_START_PAYLOAD, Cmd
from bot.loader import content, notifier, repository, state_dispenser
from bot.monitoring import monitored
from bot.rules import Command

labeler = BotLabeler()


@labeler.message(Command(Cmd.MENU, texts=texts.MENU_ALIASES, payloads=[VK_START_PAYLOAD]))
@monitored
async def start(message: Message) -> None:
    await state_dispenser.delete(message.peer_id)
    await message.answer(
        texts.welcome(len(content.questions)),
        keyboard=keyboards.main_menu(),
    )


@labeler.message(Command(Cmd.HELP, texts=texts.HELP_ALIASES))
@monitored
async def show_help(message: Message) -> None:
    await message.answer(
        texts.help_text(len(content.questions)),
        keyboard=keyboards.main_menu(),
    )


@labeler.message(Command(Cmd.CANCEL, texts=texts.CANCEL_ALIASES))
@monitored
async def cancel(message: Message) -> None:
    await state_dispenser.delete(message.peer_id)
    await message.answer(texts.CANCELLED, keyboard=keyboards.main_menu())


@labeler.message(Command(texts=texts.STATS_ALIASES))
@monitored
async def show_stats(message: Message) -> None:
    # Для обычных пользователей команды как будто не существует
    if not notifier.is_admin(message.from_id):
        await message.answer(texts.UNKNOWN)
        return

    stats = await repository.get_stats()
    names = {animal.id: animal.name for animal in content.animals.values()}
    await message.answer(texts.stats(stats, names))
