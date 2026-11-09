"""Общие объекты бота: настройки, API, хранилище состояний, сервисы.

Создаются один раз при импорте модуля и используются во всех обработчиках.
"""

from vkbottle import API, BuiltinStateDispenser

from bot.config import get_settings
from bot.db.repository import Repository
from bot.db.session import create_engine, create_session_factory
from bot.services.content import load_content
from bot.services.notifier import AdminNotifier
from bot.services.photos import PhotoService

settings = get_settings()

api = API(settings.vk_token.get_secret_value())
state_dispenser = BuiltinStateDispenser()

content = load_content(
    settings.questions_path,
    settings.animals_path,
    settings.images_dir,
)

engine = create_engine(settings.database_url)
repository = Repository(create_session_factory(engine))

photo_service = PhotoService(api, repository, settings.images_dir)
notifier = AdminNotifier(api, settings.admin_vk_id)
