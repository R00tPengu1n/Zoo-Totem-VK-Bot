"""Все тексты, которые видит пользователь.

Тексты собраны в одном месте, чтобы их было удобно редактировать,
не разбираясь в логике обработчиков.
"""

from bot.db.repository import Stats
from bot.services.content import Animal

# Подписи кнопок (не длиннее 40 символов — ограничение VK)
BTN_START_QUIZ = "Пройти викторину"
BTN_GUARDIANSHIP = "Узнать об опеке"
BTN_HELP = "Помощь"
BTN_SHARE = "Поделиться"
BTN_CONTACT = "Связаться с сотрудником"
BTN_FEEDBACK = "Оставить отзыв"
BTN_RETRY = "Попробовать ещё раз?"
BTN_CANCEL = "Отмена"
BTN_STOP_QUIZ = "Выйти из викторины"
BTN_BECOME_GUARDIAN = "Стать опекуном"
BTN_SHARE_VK = "Поделиться ВКонтакте"
BTN_SHARE_TELEGRAM = "Поделиться в Telegram"

# Тексты, которые пользователь может набрать вручную вместо нажатия кнопок
MENU_ALIASES = ("/start", "start", "начать", "старт", "меню", "/menu", "привет")
HELP_ALIASES = ("/help", "помощь", "помоги", "help")
CANCEL_ALIASES = ("/cancel", "отмена", "отменить", "выйти из викторины")
QUIZ_ALIASES = ("/quiz", "викторина", BTN_START_QUIZ, BTN_RETRY, "попробовать ещё раз")
GUARDIANSHIP_ALIASES = ("/guardianship", "опека", "об опеке", BTN_GUARDIANSHIP)
SHARE_ALIASES = ("/share", BTN_SHARE)
CONTACT_ALIASES = ("/contact", BTN_CONTACT, "сотрудник")
FEEDBACK_ALIASES = ("/feedback", BTN_FEEDBACK, "отзыв")
STATS_ALIASES = ("/stats",)

MAX_USER_TEXT_LENGTH = 2000


def welcome(questions_count: int) -> str:
    return (
        "Привет! 👋\n\n"
        "Давай узнаем, какое животное Московского зоопарка — твоё тотемное. "
        f"Тебя ждут {questions_count} вопросов: отвечай честно, "
        "правильных и неправильных ответов здесь нет.\n\n"
        "А в конце я расскажу, как стать опекуном своего зверя "
        "и помочь зоопарку заботиться о нём.\n\n"
        f"Жми «{BTN_START_QUIZ}», чтобы начать!"
    )


def help_text(questions_count: int) -> str:
    return (
        "Вот что я умею:\n\n"
        f"🦁 «{BTN_START_QUIZ}» — ответь на {questions_count} вопросов кнопками, "
        "и я подберу твоё тотемное животное.\n\n"
        "🐾 После результата можно узнать о программе опеки, поделиться "
        "результатом с друзьями, задать вопрос сотруднику зоопарка "
        "или оставить отзыв.\n\n"
        f"↩️ «{BTN_CANCEL}» или /cancel — выйти из текущего действия.\n"
        "🏠 «Меню» или /start — вернуться в начало.\n\n"
        "Если кнопки пропали, просто напиши «Меню»."
    )


MAIN_MENU = "Ты в главном меню. Выбирай, с чего начнём 👇"
CANCELLED = "Хорошо, отменил. Возвращаю в меню 👇"


def question(index: int, total: int, text: str) -> str:
    return f"Вопрос {index + 1} из {total}\n\n{text}"


USE_BUTTONS = "Выбери вариант ответа кнопкой 👇"
OUTDATED_BUTTON = "Это кнопка от другого вопроса. Вот текущий 👇"


def result(animal: Animal) -> str:
    return (
        f"🎉 {animal.headline}\n\n"
        f"Твоё тотемное животное в Московском зоопарке — {animal.name}.\n\n"
        f"{animal.description}\n\n"
        f"🔎 Интересный факт: {animal.fact}\n\n"
        "Это животное живёт в Московском зоопарке, и его можно взять "
        f"под опеку. Нажми «{BTN_GUARDIANSHIP}», чтобы узнать, как это сделать."
    )


def guardianship(animal: Animal | None) -> str:
    intro = (
        f"🐾 Твоё тотемное животное — {animal.name}, и ты можешь стать его опекуном!\n\n"
        if animal
        else "🐾 Программа «Возьми животное под опеку»\n\n"
    )
    return (
        intro
        + "В Московском зоопарке живут около 6 тысяч животных примерно "
        "1 100 видов. Каждое из них требует внимания и ухода. Программа опеки "
        "позволяет пожертвованием на любую сумму помочь зоопарку заботиться "
        "о его обитателях и сохранять биоразнообразие планеты.\n\n"
        "Стоимость опеки рассчитывается из ежедневного рациона животного. "
        "Опекуном может стать любой: и человек, и большая компания.\n\n"
        "Что получает опекун:\n"
        "• почётный статус и возможность круглый год навещать подопечного\n"
        "• новости о жизни и самочувствии животного\n"
        "• табличку со своим именем у вольера\n\n"
        "Подробности и заявка — по кнопке ниже. Остались вопросы? "
        f"Нажми «{BTN_CONTACT}», и сотрудник зоопарка всё расскажет."
    )


NO_RESULT_YET = (
    "Сначала пройди викторину — без результата делиться пока нечем 🙂"
)


def share_text(animal: Animal) -> str:
    return (
        f"Моё тотемное животное в Московском зоопарке — {animal.name}! "
        "А какое у тебя?"
    )


def share_message(animal: Animal, bot_link: str) -> str:
    return (
        "Поделись результатом с друзьями — кнопки ниже откроют окно публикации "
        "со ссылкой на викторину. Или просто скопируй текст:\n\n"
        f"{share_text(animal)} Пройди викторину: {bot_link}"
    )


CONTACT_PROMPT = (
    "Напиши свой вопрос одним сообщением, и я передам его сотруднику зоопарка "
    "вместе с результатом твоей викторины. Ответ придёт сюда, в сообщения "
    "сообщества.\n\n"
    f"Передумал? Нажми «{BTN_CANCEL}»."
)
CONTACT_SENT = (
    "Готово! Вопрос передан сотруднику зоопарка. Ответ придёт в этот диалог 🙌"
)


def contact_failed(email: str) -> str:
    return (
        "Не получилось передать вопрос: что-то пошло не так на нашей стороне 😔\n"
        f"Попробуй позже или напиши на почту {email}."
    )


def admin_message(
    user_id: int,
    user_name: str,
    animal: Animal | None,
    text: str,
) -> str:
    result_line = animal.name if animal else "ещё не проходил"
    return (
        "📩 Новый вопрос из бота-викторины\n\n"
        f"От: {user_name} (https://vk.com/id{user_id})\n"
        f"Результат викторины: {result_line}\n\n"
        f"Вопрос:\n{text}"
    )


FEEDBACK_PROMPT = (
    "Расскажи, как тебе викторина: что понравилось, а что стоит улучшить? "
    "Напиши отзыв одним сообщением.\n\n"
    f"Передумал? Нажми «{BTN_CANCEL}»."
)
FEEDBACK_SAVED = "Спасибо за отзыв! Он поможет сделать викторину лучше 💚"

TEXT_REQUIRED = "Пожалуйста, напиши ответ текстом 🙂"
TEXT_TOO_LONG = (
    f"Получилось слишком длинно. Уложись, пожалуйста, в {MAX_USER_TEXT_LENGTH} символов."
)

UNKNOWN = (
    "Я пока не понимаю такие сообщения 🙈\n"
    "Воспользуйся кнопками или напиши «Помощь»."
)
ERROR = "Ой, что-то пошло не так 😔 Попробуй ещё раз или напиши «Меню»."


def stats(data: Stats, names: dict[str, str]) -> str:
    lines = [
        "📊 Статистика викторины\n",
        f"Прохождений: {data.total_results}",
        f"Уникальных пользователей: {data.unique_users}",
        f"Отзывов: {data.feedback_count}",
    ]
    if data.results_by_animal:
        lines.append("\nРезультаты:")
        lines.extend(
            f"• {names.get(animal_id, animal_id)} — {count}"
            for animal_id, count in data.results_by_animal
        )
    return "\n".join(lines)
