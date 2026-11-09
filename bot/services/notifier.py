"""Пересылка вопросов пользователей сотруднику зоопарка."""

import logging

from vkbottle import API, VKAPIError

logger = logging.getLogger(__name__)


class AdminNotifier:
    def __init__(self, api: API, admin: str) -> None:
        self._api = api
        self._admin = admin.strip()
        self.admin_id: int | None = None

    async def resolve_admin(self) -> None:
        """Превращает короткое имя из настроек (например, `durov`) в числовой id.

        Вызывается один раз при запуске бота. Если не получилось, бот всё
        равно запустится, но пересылка вопросов работать не будет.
        """
        if self._admin.lstrip("-").isdigit():
            self.admin_id = int(self._admin)
            return

        screen_name = self._admin.rsplit("/", maxsplit=1)[-1]
        try:
            users = await self._api.users.get(user_ids=[screen_name])
        except VKAPIError:
            logger.exception("Не удалось найти сотрудника VK «%s»", screen_name)
            return

        if not users:
            logger.error("Сотрудник VK «%s» не найден", screen_name)
            return

        self.admin_id = users[0].id
        logger.info("Вопросы будут пересылаться пользователю id%s", self.admin_id)

    def is_admin(self, user_id: int) -> bool:
        return self.admin_id is not None and user_id == self.admin_id

    async def get_user_name(self, user_id: int) -> str:
        """Имя пользователя для письма сотруднику. В базу оно не сохраняется."""
        try:
            users = await self._api.users.get(user_ids=[user_id])
        except VKAPIError:
            logger.warning("Не удалось получить имя пользователя id%s", user_id)
            return f"id{user_id}"
        if not users:
            return f"id{user_id}"
        return f"{users[0].first_name} {users[0].last_name}"

    async def send(self, text: str) -> bool:
        """Отправляет сообщение сотруднику. Возвращает True, если получилось."""
        if self.admin_id is None:
            logger.error("Сотрудник для пересылки не настроен (ADMIN_VK_ID)")
            return False

        try:
            await self._api.messages.send(
                peer_id=self.admin_id,
                message=text,
                random_id=0,
            )
        except VKAPIError:
            logger.exception("Не удалось отправить сообщение сотруднику")
            return False
        return True
