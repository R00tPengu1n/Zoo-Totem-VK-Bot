import json
from pathlib import Path

import pytest

from bot.services.content import ContentError, load_content
from bot.services.quiz_engine import add_answer, pick_animal

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

ANIMALS = [
    {
        "id": "lion",
        "name": "лев",
        "headline": "Да ты лев!",
        "description": "Описание",
        "fact": "Факт",
        "image": "lion.jpg",
    }
]


def write_json(path: Path, data: object) -> Path:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def make_questions(weights: dict[str, int]) -> list[dict]:
    return [
        {
            "id": "q1",
            "text": "Вопрос",
            "options": [
                {"text": "Ответ 1", "weights": weights},
                {"text": "Ответ 2", "weights": weights},
            ],
        }
    ]


def test_project_content_is_valid():
    content = load_content(
        DATA_DIR / "questions.json",
        DATA_DIR / "animals.json",
        DATA_DIR / "images",
        check_images=False,
    )

    assert len(content.animals) == 10
    assert len(content.questions) >= 5


def test_project_images_exist():
    load_content(
        DATA_DIR / "questions.json",
        DATA_DIR / "animals.json",
        DATA_DIR / "images",
    )


def test_every_animal_can_win():
    content = load_content(
        DATA_DIR / "questions.json",
        DATA_DIR / "animals.json",
        DATA_DIR / "images",
        check_images=False,
    )

    for animal_id in content.animal_ids:
        scores: dict[str, int] = {}
        for question in content.questions:
            best_option = max(
                question.options,
                key=lambda option: option.weights.get(animal_id, 0),
            )
            scores = add_answer(scores, best_option.weights)

        best = max(scores.values())
        assert scores.get(animal_id) == best, f"«{animal_id}» не может победить"
        assert pick_animal(scores, content.animal_ids) is not None


def test_unknown_animal_in_weights_is_rejected(tmp_path):
    questions = write_json(tmp_path / "q.json", make_questions({"tiger": 1}))
    animals = write_json(tmp_path / "a.json", ANIMALS)

    with pytest.raises(ContentError, match="tiger"):
        load_content(questions, animals, tmp_path, check_images=False)


def test_too_long_button_label_is_rejected(tmp_path):
    data = make_questions({"lion": 1})
    data[0]["options"][0]["text"] = "Очень длинный ответ, который не влезет в кнопку VK"
    questions = write_json(tmp_path / "q.json", data)
    animals = write_json(tmp_path / "a.json", ANIMALS)

    with pytest.raises(ContentError):
        load_content(questions, animals, tmp_path, check_images=False)


def test_missing_image_is_rejected(tmp_path):
    questions = write_json(tmp_path / "q.json", make_questions({"lion": 1}))
    animals = write_json(tmp_path / "a.json", ANIMALS)

    with pytest.raises(ContentError, match="фотографии"):
        load_content(questions, animals, tmp_path)


def test_broken_json_is_rejected(tmp_path):
    questions = tmp_path / "q.json"
    questions.write_text("{not json", encoding="utf-8")
    animals = write_json(tmp_path / "a.json", ANIMALS)

    with pytest.raises(ContentError, match="JSON"):
        load_content(questions, animals, tmp_path)
