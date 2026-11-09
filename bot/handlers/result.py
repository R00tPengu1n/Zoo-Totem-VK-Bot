"""Действия после викторины: рассказ об опеке и «Поделиться»."""

from vkbottle.bot import BotLabeler, Message

from bot import keyboards, texts
from bot.keyboards import Cmd
from bot.loader import content, repository, settings
from bot.monitoring import monitored
from bot.rules import Command
from bot.services.content import Animal

labeler = BotLabeler()


async def get_last_animal(user_id: int) -> Animal | None:
    """Последний результат пользователя или None, если он ещё не играл."""
    animal_id = await repository.get_last_result(user_id)
    if animal_id is None:
        return None
    # Животное могли убрать из контента — тогда считаем, что результата нет
    return content.animals.get(animal_id)


async def keyboard_after_action(user_id: int) -> str:
    """Какую клавиатуру вернуть после отзыва или вопроса сотруднику."""
    if await get_last_animal(user_id) is None:
        return keyboards.main_menu()
    return keyboards.result()


@labeler.message(Command(Cmd.GUARDIANSHIP, texts=texts.GUARDIANSHIP_ALIASES))
@monitored
async def show_guardianship(message: Message) -> None:
    animal = await get_last_animal(message.from_id)
    await message.answer(
        texts.guardianship(animal),
        keyboard=keyboards.guardianship_link(settings.guardianship_url),
    )


@labeler.message(Command(Cmd.SHARE, texts=texts.SHARE_ALIASES))
@monitored
async def share_result(message: Message) -> None:
    animal = await get_last_animal(message.from_id)
    if animal is None:
        await message.answer(texts.NO_RESULT_YET, keyboard=keyboards.main_menu())
        return

    await message.answer(
        texts.share_message(animal, settings.bot_link),
        keyboard=keyboards.share_links(texts.share_text(animal), settings.bot_link),
    )
