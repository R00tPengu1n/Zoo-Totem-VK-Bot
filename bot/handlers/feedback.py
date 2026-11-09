"""Сбор отзывов пользователей."""

import logging

from vkbottle.bot import BotLabeler, Message
from vkbottle.dispatch.rules.base import StateRule

from bot import keyboards, texts
from bot.handlers.result import keyboard_after_action
from bot.keyboards import Cmd
from bot.loader import repository, state_dispenser
from bot.monitoring import monitored
from bot.rules import Command
from bot.states import DialogState

logger = logging.getLogger(__name__)

labeler = BotLabeler()


@labeler.message(Command(Cmd.FEEDBACK, texts=texts.FEEDBACK_ALIASES))
@monitored
async def ask_feedback(message: Message) -> None:
    await state_dispenser.set(message.peer_id, DialogState.WAITING_FEEDBACK)
    await message.answer(texts.FEEDBACK_PROMPT, keyboard=keyboards.cancel())


@labeler.message(StateRule(DialogState.WAITING_FEEDBACK))
@monitored
async def save_feedback(message: Message) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer(texts.TEXT_REQUIRED, keyboard=keyboards.cancel())
        return
    if len(text) > texts.MAX_USER_TEXT_LENGTH:
        await message.answer(texts.TEXT_TOO_LONG, keyboard=keyboards.cancel())
        return

    await repository.save_feedback(message.from_id, text)
    logger.info("Новый отзыв от пользователя id%s", message.from_id)

    await state_dispenser.delete(message.peer_id)
    await message.answer(
        texts.FEEDBACK_SAVED,
        keyboard=await keyboard_after_action(message.from_id),
    )
