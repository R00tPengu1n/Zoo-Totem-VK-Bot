"""Общая настройка тестов.

Модуль bot.loader при импорте читает настройки. Чтобы тесты обработчиков
работали без файла .env (например, в CI) и никогда не ходили в настоящий VK,
подставляем выдуманные значения через переменные окружения: они важнее .env.
"""

import os

os.environ["VK_TOKEN"] = "test-token"
os.environ["ADMIN_VK_ID"] = "1"
os.environ["BOT_LINK"] = "https://vk.me/club1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
