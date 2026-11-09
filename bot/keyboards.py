"""Клавиатуры бота.

Каждая кнопка отправляет payload с командой — по ней обработчик понимает,
какая кнопка нажата, даже если текст на кнопке когда-нибудь поменяется.
"""

from urllib.parse import urlencode

from vkbottle import Keyboard, KeyboardButtonColor, OpenLink, Text

from bot import texts
from bot.services.content import Question


class Cmd:
    """Команды, которые передаются в payload кнопок."""

    MENU = "menu"
    HELP = "help"
    CANCEL = "cancel"
    QUIZ_START = "quiz:start"
    ANSWER = "quiz:answer"
    GUARDIANSHIP = "guardianship"
    SHARE = "share"
    CONTACT = "contact"
    FEEDBACK = "feedback"


# Payload кнопки «Начать», которую VK показывает в новом диалоге с сообществом
VK_START_PAYLOAD = {"command": "start"}


def _button(label: str, cmd: str, **extra: int) -> Text:
    return Text(label, payload={"cmd": cmd, **extra})


def main_menu() -> str:
    return (
        Keyboard(one_time=False)
        .add(_button(texts.BTN_START_QUIZ, Cmd.QUIZ_START), color=KeyboardButtonColor.POSITIVE)
        .row()
        .add(_button(texts.BTN_GUARDIANSHIP, Cmd.GUARDIANSHIP))
        .add(_button(texts.BTN_HELP, Cmd.HELP))
        .get_json()
    )


def question(question: Question, question_index: int) -> str:
    keyboard = Keyboard(one_time=False)
    for option_index, option in enumerate(question.options):
        keyboard.add(
            _button(option.text, Cmd.ANSWER, q=question_index, a=option_index),
            color=KeyboardButtonColor.PRIMARY,
        )
        keyboard.row()
    keyboard.add(_button(texts.BTN_STOP_QUIZ, Cmd.CANCEL), color=KeyboardButtonColor.SECONDARY)
    return keyboard.get_json()


def result() -> str:
    return (
        Keyboard(one_time=False)
        .add(_button(texts.BTN_GUARDIANSHIP, Cmd.GUARDIANSHIP), color=KeyboardButtonColor.POSITIVE)
        .add(_button(texts.BTN_SHARE, Cmd.SHARE), color=KeyboardButtonColor.PRIMARY)
        .row()
        .add(_button(texts.BTN_CONTACT, Cmd.CONTACT))
        .row()
        .add(_button(texts.BTN_FEEDBACK, Cmd.FEEDBACK))
        .row()
        .add(_button(texts.BTN_RETRY, Cmd.QUIZ_START))
        .get_json()
    )


def cancel() -> str:
    return (
        Keyboard(one_time=False)
        .add(_button(texts.BTN_CANCEL, Cmd.CANCEL), color=KeyboardButtonColor.NEGATIVE)
        .get_json()
    )


def guardianship_link(url: str) -> str:
    """Кнопка-ссылка прямо под сообщением (inline-клавиатура)."""
    return Keyboard(inline=True).add(OpenLink(url, texts.BTN_BECOME_GUARDIAN)).get_json()


def share_links(share_text: str, bot_link: str) -> str:
    vk_url = "https://vk.com/share.php?" + urlencode({"url": bot_link, "title": share_text})
    telegram_url = "https://t.me/share/url?" + urlencode({"url": bot_link, "text": share_text})
    return (
        Keyboard(inline=True)
        .add(OpenLink(vk_url, texts.BTN_SHARE_VK))
        .row()
        .add(OpenLink(telegram_url, texts.BTN_SHARE_TELEGRAM))
        .get_json()
    )
