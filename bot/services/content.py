"""Загрузка и проверка контента викторины: вопросов и животных.

Контент хранится в JSON-файлах, поэтому его можно менять без правки кода.
При запуске бота файлы проверяются Pydantic-моделями: если в них ошибка,
бот не запустится и сообщит, что именно не так.
"""

import json
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator

# Ограничение VK на длину подписи кнопки
MAX_BUTTON_LABEL_LENGTH = 40


class ContentError(Exception):
    """Ошибка в файлах с вопросами или животными."""


class Animal(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    description: str = Field(min_length=1)
    fact: str = Field(min_length=1)
    image: str = Field(min_length=1)


class AnswerOption(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_BUTTON_LABEL_LENGTH)
    weights: dict[str, int] = Field(min_length=1)

    @field_validator("weights")
    @classmethod
    def weights_must_be_positive(cls, weights: dict[str, int]) -> dict[str, int]:
        if any(points <= 0 for points in weights.values()):
            raise ValueError("Баллы за ответ должны быть положительными")
        return weights


class Question(BaseModel):
    id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    options: list[AnswerOption] = Field(min_length=2, max_length=6)


class QuizContent(BaseModel):
    questions: list[Question] = Field(min_length=1)
    animals: dict[str, Animal]

    @property
    def animal_ids(self) -> list[str]:
        return list(self.animals)

    def get_animal(self, animal_id: str) -> Animal:
        return self.animals[animal_id]


def _read_json(path: Path) -> object:
    try:
        with path.open(encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        raise ContentError(f"Файл не найден: {path}") from None
    except json.JSONDecodeError as error:
        raise ContentError(f"Некорректный JSON в {path}: {error}") from error


def _check_consistency(content: QuizContent, images_dir: Path | None) -> None:
    question_ids = [question.id for question in content.questions]
    if len(question_ids) != len(set(question_ids)):
        raise ContentError("У вопросов повторяются id")

    for question in content.questions:
        for option in question.options:
            unknown = set(option.weights) - set(content.animals)
            if unknown:
                raise ContentError(
                    f"Вопрос «{question.id}», ответ «{option.text}»: "
                    f"неизвестные животные {sorted(unknown)}"
                )

    if images_dir is None:
        return

    for animal in content.animals.values():
        if not (images_dir / animal.image).is_file():
            raise ContentError(
                f"Нет фотографии для животного «{animal.id}»: "
                f"{images_dir / animal.image}"
            )


def load_content(
    questions_path: Path,
    animals_path: Path,
    images_dir: Path,
    *,
    check_images: bool = True,
) -> QuizContent:
    """Читает JSON-файлы, проверяет их и возвращает контент викторины."""
    raw_questions = _read_json(questions_path)
    raw_animals = _read_json(animals_path)

    try:
        animals = [Animal.model_validate(item) for item in raw_animals]
        questions = [Question.model_validate(item) for item in raw_questions]
    except (ValidationError, TypeError) as error:
        raise ContentError(f"Ошибка в контенте викторины: {error}") from error

    animals_by_id = {animal.id: animal for animal in animals}
    if len(animals_by_id) != len(animals):
        raise ContentError("У животных повторяются id")

    content = QuizContent(questions=questions, animals=animals_by_id)
    _check_consistency(content, images_dir if check_images else None)
    return content
