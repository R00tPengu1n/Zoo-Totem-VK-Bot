"""Запросы к базе данных.

Обработчики не работают с SQLAlchemy напрямую: все запросы собраны здесь.
Так код обработчиков проще читать, а запросы легко менять в одном месте.
"""

from dataclasses import dataclass

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.db.models import Feedback, PhotoCache, QuizResult


@dataclass(frozen=True)
class Stats:
    total_results: int
    unique_users: int
    feedback_count: int
    results_by_animal: list[tuple[str, int]]


class Repository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save_result(self, user_id: int, animal_id: str) -> None:
        async with self._session_factory() as session:
            session.add(QuizResult(user_id=user_id, animal_id=animal_id))
            await session.commit()

    async def get_last_result(self, user_id: int) -> str | None:
        async with self._session_factory() as session:
            query = (
                select(QuizResult.animal_id)
                .where(QuizResult.user_id == user_id)
                .order_by(QuizResult.id.desc())
                .limit(1)
            )
            return await session.scalar(query)

    async def save_feedback(self, user_id: int, text: str) -> None:
        async with self._session_factory() as session:
            session.add(Feedback(user_id=user_id, text=text))
            await session.commit()

    async def get_cached_photo(self, animal_id: str, file_hash: str) -> str | None:
        async with self._session_factory() as session:
            cached = await session.get(PhotoCache, animal_id)
            if cached is None or cached.file_hash != file_hash:
                return None
            return cached.attachment

    async def save_cached_photo(
        self, animal_id: str, file_hash: str, attachment: str
    ) -> None:
        async with self._session_factory() as session:
            await session.merge(
                PhotoCache(
                    animal_id=animal_id,
                    file_hash=file_hash,
                    attachment=attachment,
                )
            )
            await session.commit()

    async def get_stats(self) -> Stats:
        async with self._session_factory() as session:
            total_results = await session.scalar(select(func.count(QuizResult.id)))
            unique_users = await session.scalar(
                select(func.count(distinct(QuizResult.user_id)))
            )
            feedback_count = await session.scalar(select(func.count(Feedback.id)))

            count_column = func.count(QuizResult.id).label("count")
            rows = await session.execute(
                select(QuizResult.animal_id, count_column)
                .group_by(QuizResult.animal_id)
                .order_by(count_column.desc())
            )

        return Stats(
            total_results=total_results or 0,
            unique_users=unique_users or 0,
            feedback_count=feedback_count or 0,
            results_by_animal=[(animal_id, count) for animal_id, count in rows],
        )
