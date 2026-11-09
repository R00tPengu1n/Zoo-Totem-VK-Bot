"""Связь с сотрудником зоопарка.

Пользователь пишет вопрос, а бот пересылает его сотруднику вместе
с результатом викторины, чтобы сотрудник сразу понимал контекст.
"""

from vkbottle.bot import BotLabeler, Message
from vkbottle.dispatch.rules.base import StateRule

from bot import keyboards, texts
from bot.handlers.result import get_last_animal, keyboard_after_action
from bot.keyboards import Cmd
from bot.loader import notifier, settings, state_dispenser
from bot.monitoring import monitored
from bot.rules import Command
from bot.states import DialogState

labeler = BotLabeler()


@labeler.message(Command(Cmd.CONTACT, texts=texts.CONTACT_ALIASES))
@monitored
async def ask_question(message: Message) -> None:
    await state_dispenser.set(message.peer_id, DialogState.WAITING_CONTACT_MESSAGE)
    await message.answer(texts.CONTACT_PROMPT, keyboard=keyboards.cancel())


@labeler.message(StateRule(DialogState.WAITING_CONTACT_MESSAGE))
@monitored
async def forward_question(message: Message) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer(texts.TEXT_REQUIRED, keyboard=keyboards.cancel())
        return
    if len(text) > texts.MAX_USER_TEXT_LENGTH:
        await message.answer(texts.TEXT_TOO_LONG, keyboard=keyboards.cancel())
        return

    animal = await get_last_animal(message.from_id)
    user_name = await notifier.get_user_name(message.from_id)
    is_sent = await notifier.send(texts.admin_message(message.from_id, user_name, animal, text))

    await state_dispenser.delete(message.peer_id)
    reply = texts.CONTACT_SENT if is_sent else texts.contact_failed(settings.contact_email)
    await message.answer(reply, keyboard=await keyboard_after_action(message.from_id))
