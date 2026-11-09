"""Обработчики сообщений.

Порядок в списке важен: vkbottle проверяет обработчики по очереди
и запускает первый подходящий. Поэтому общие команды («Меню», «Отмена»)
идут первыми, а обработчик непонятных сообщений — последним.
"""

from bot.handlers import common, contact, fallback, feedback, quiz, result

labelers = [
    common.labeler,
    quiz.labeler,
    result.labeler,
    contact.labeler,
    feedback.labeler,
    fallback.labeler,
]

__all__ = ["labelers"]
