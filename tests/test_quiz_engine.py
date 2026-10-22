import random

import pytest

from bot.services.quiz_engine import add_answer, pick_animal


def test_add_answer_sums_points():
    scores = add_answer({"lion": 2}, {"lion": 1, "manul": 3})

    assert scores == {"lion": 3, "manul": 3}


def test_add_answer_does_not_modify_original_scores():
    original = {"lion": 2}

    add_answer(original, {"lion": 5})

    assert original == {"lion": 2}


def test_pick_animal_returns_leader():
    scores = {"lion": 5, "manul": 2, "meerkat": 4}

    assert pick_animal(scores, ["lion", "manul", "meerkat"]) == "lion"


def test_pick_animal_breaks_tie_between_leaders_only():
    scores = {"lion": 5, "manul": 5, "meerkat": 1}
    rng = random.Random(42)

    results = {pick_animal(scores, ["lion", "manul", "meerkat"], rng) for _ in range(100)}

    assert results == {"lion", "manul"}


def test_pick_animal_ignores_unknown_animals():
    scores = {"removed_animal": 100, "lion": 1}

    assert pick_animal(scores, ["lion", "manul"]) == "lion"


def test_pick_animal_with_empty_scores_picks_any_known_animal():
    assert pick_animal({}, ["lion", "manul"]) in {"lion", "manul"}


def test_pick_animal_requires_animals():
    with pytest.raises(ValueError):
        pick_animal({"lion": 1}, [])
