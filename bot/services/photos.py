"""Загрузка фотографий животных на сервер VK.

Чтобы отправить фото в сообщении, его нужно сначала загрузить в VK:
1. photos.getMessagesUploadServer — получить адрес для загрузки;
2. POST-запрос с файлом на этот адрес;
3. photos.saveMessagesPhoto — сохранить фото и получить его id.

Загрузка занимает время, поэтому результат кэшируется в базе данных:
каждое фото загружается один раз и дальше переиспользуется.
"""

import asyncio
import hashlib
import logging
from pathlib import Path

import aiohttp
from vkbottle import API

from bot.db.repository import Repository
from bot.services.content import Animal

logger = logging.getLogger(__name__)

UPLOAD_TIMEOUT = aiohttp.ClientTimeout(total=30)


class PhotoUploadError(Exception):
    """Не удалось загрузить фотографию в VK."""


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PhotoService:
    def __init__(self, api: API, repository: Repository, images_dir: Path) -> None:
        self._api = api
        self._repository = repository
        self._images_dir = images_dir
        # Одна блокировка на каждое животное: если два пользователя одновременно
        # получат одно и то же животное, фото загрузится только один раз.
        self._locks: dict[str, asyncio.Lock] = {}

    async def get_attachment(self, animal: Animal, peer_id: int) -> str | None:
        """Возвращает строку вложения вида photo-123_456 или None при ошибке.

        Ошибка загрузки фото не должна ломать викторину: в этом случае
        пользователь получит результат без картинки, а ошибка попадёт в лог.
        """
        path = self._images_dir / animal.image
        lock = self._locks.setdefault(animal.id, asyncio.Lock())

        async with lock:
            try:
                file_hash = file_sha256(path)
                cached = await self._repository.get_cached_photo(animal.id, file_hash)
                if cached:
                    return cached

                attachment = await self._upload(path, peer_id)
                await self._repository.save_cached_photo(
                    animal.id, file_hash, attachment
                )
                logger.info("Фото «%s» загружено в VK: %s", animal.id, attachment)
                return attachment
            except Exception:
                logger.exception("Не удалось подготовить фото для «%s»", animal.id)
                return None

    async def _upload(self, path: Path, peer_id: int) -> str:
        server = await self._api.photos.get_messages_upload_server(peer_id=peer_id)

        form = aiohttp.FormData()
        form.add_field(
            "photo",
            path.read_bytes(),
            filename=path.name,
            content_type="image/jpeg",
        )

        async with aiohttp.ClientSession(timeout=UPLOAD_TIMEOUT) as session:
            async with session.post(server.upload_url, data=form) as response:
                response.raise_for_status()
                # VK отвечает JSON-ом, но иногда с типом text/html
                uploaded = await response.json(content_type=None)

        if not uploaded.get("photo") or uploaded.get("photo") == "[]":
            raise PhotoUploadError(f"VK не принял файл {path.name}: {uploaded}")

        saved = await self._api.photos.save_messages_photo(
            photo=uploaded["photo"],
            server=uploaded["server"],
            hash=uploaded["hash"],
        )
        photo = saved[0]

        attachment = f"photo{photo.owner_id}_{photo.id}"
        if photo.access_key:
            attachment += f"_{photo.access_key}"
        return attachment
