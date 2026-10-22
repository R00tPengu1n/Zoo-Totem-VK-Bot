"""Таблицы базы данных.

Храним только то, что нужно для работы бота: VK id пользователя,
результат викторины и текст отзыва. Имена, телефоны и другие
персональные данные бот не сохраняет.
"""

from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class QuizResult(Base):
    __tablename__ = "quiz_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    animal_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )


class PhotoCache(Base):
    """Фото, уже загруженные на сервер VK.

    `file_hash` позволяет заметить, что картинку в data/images заменили,
    и загрузить новую версию вместо устаревшей.
    """

    __tablename__ = "photo_cache"

    animal_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    file_hash: Mapped[str] = mapped_column(String(64))
    attachment: Mapped[str] = mapped_column(String(255))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
