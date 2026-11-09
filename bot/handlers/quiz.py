"""Прохождение викторины: вопросы, ответы и итоговый результат."""

import asyncio

from vkbottle.bot import BotLabeler, Message
from vkbottle.dispatch.rules.base import StateRule

from bot import keyboards, texts
from bot.keyboards import Cmd
from bot.loader import content, photo_service, repository, state_dispenser
from bot.monitoring import monitored
from bot.rules import AnswerButton, Command
from bot.services.quiz_engine import Scores, add_answer, pick_animal
from bot.states import DialogState

labeler = BotLabeler()

# Одна блокировка на каждый диалог: если пользователь быстро нажмёт кнопку
# дважды, ответы обработаются по очереди, а не параллельно с одним и тем же
# состоянием (иначе результат мог бы сохраниться дважды).
_answer_locks: dict[int, asyncio.Lock] = {}


async def send_question(message: Message, question_index: int) -> None:
    question = content.questions[question_index]
    await message.answer(
        texts.question(question_index, len(content.questions), question.text),
        keyboard=keyboards.question(question, question_index),
    )


async def send_result(message: Message, scores: Scores) -> None:
    animal_id = pick_animal(scores, content.animal_ids)
    animal = content.get_animal(animal_id)

    await repository.save_result(message.from_id, animal_id)
    attachment = await photo_service.get_attachment(animal, message.peer_id)

    await message.answer(
        texts.result(animal),
        attachment=attachment,
        keyboard=keyboards.result(),
    )


@labeler.message(Command(Cmd.QUIZ_START, texts=texts.QUIZ_ALIASES))
@monitored
async def start_quiz(message: Message) -> None:
    await state_dispenser.set(
        message.peer_id,
        DialogState.ANSWERING,
        question_index=0,
        scores={},
    )
    await send_question(message, 0)


@labeler.message(AnswerButton(Cmd.ANSWER), StateRule(DialogState.ANSWERING))
@monitored
async def handle_answer(
    message: Message,
    question_index: int,
    option_index: int,
) -> None:
    lock = _answer_locks.setdefault(message.peer_id, asyncio.Lock())
    async with lock:
        state = await state_dispenser.get(message.peer_id)
        # Викторину уже завершило предыдущее нажатие, пока мы ждали своей очереди
        if state is None:
            return
        payload = state.payload
        current_index: int = payload.get("question_index", 0)

        # Пользователь нажал кнопку под старым сообщением — показываем актуальный вопрос
        if question_index != current_index:
            await message.answer(texts.OUTDATED_BUTTON)
            await send_question(message, current_index)
            return

        question = content.questions[current_index]
        if not 0 <= option_index < len(question.options):
            await send_question(message, current_index)
            return

        scores = add_answer(payload.get("scores", {}), question.options[option_index].weights)
        next_index = current_index + 1

        if next_index < len(content.questions):
            await state_dispenser.set(
                message.peer_id,
                DialogState.ANSWERING,
                question_index=next_index,
                scores=scores,
            )
            await send_question(message, next_index)
            return

        await state_dispenser.delete(message.peer_id)
        await send_result(message, scores)


@labeler.message(StateRule(DialogState.ANSWERING))
@monitored
async def answer_hint(message: Message) -> None:
    """Любое другое сообщение во время викторины: напоминаем про кнопки."""
    state = await state_dispenser.get(message.peer_id)
    current_index = state.payload.get("question_index", 0) if state else 0
    await message.answer(texts.USE_BUTTONS)
    await send_question(message, current_index)
