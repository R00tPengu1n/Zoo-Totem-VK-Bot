"""Состояния диалога с пользователем."""

from vkbottle import BaseStateGroup


class DialogState(BaseStateGroup):
    # Пользователь проходит викторину. В данных состояния хранятся
    # номер текущего вопроса и набранные баллы.
    ANSWERING = "answering"
    # Бот ждёт вопрос для сотрудника зоопарка
    WAITING_CONTACT_MESSAGE = "waiting_contact_message"
    # Бот ждёт текст отзыва
    WAITING_FEEDBACK = "waiting_feedback"
