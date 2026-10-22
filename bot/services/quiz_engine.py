"""Алгоритм подсчёта результата викторины.

У каждого варианта ответа есть «веса» — сколько баллов он даёт разным
животным. Баллы суммируются по всем ответам, и побеждает животное
с наибольшей суммой. Если лидеров несколько, выбирается случайный из них.

Модуль не зависит от VK и базы данных, поэтому его легко тестировать.
"""

import random
from collections.abc import Mapping, Sequence

Scores = dict[str, int]


def add_answer(scores: Mapping[str, int], weights: Mapping[str, int]) -> Scores:
    """Возвращает новый словарь баллов с учётом очередного ответа.

    Исходный словарь не изменяется: так состояние пользователя нельзя
    случайно испортить, а функцию проще тестировать.
    """
    updated = dict(scores)
    for animal_id, points in weights.items():
        updated[animal_id] = updated.get(animal_id, 0) + points
    return updated


def pick_animal(
    scores: Mapping[str, int],
    animal_ids: Sequence[str],
    rng: random.Random | None = None,
) -> str:
    """Определяет итоговое животное по набранным баллам.

    Учитываются только животные из `animal_ids`: если в контенте
    что-то поменяли, устаревшие ключи из баллов не повлияют на результат.
    """
    if not animal_ids:
        raise ValueError("Список животных пуст")

    rng = rng or random.Random()
    known_scores = {animal_id: scores.get(animal_id, 0) for animal_id in animal_ids}
    best_score = max(known_scores.values())
    leaders = [
        animal_id
        for animal_id, score in known_scores.items()
        if score == best_score
    ]
    return rng.choice(leaders)
