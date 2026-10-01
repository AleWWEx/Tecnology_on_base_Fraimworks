"""Тесты функций работы с клубами."""

from clubs import (
    add_club,
    find_club,
    get_club,
    get_club_card,
    iter_club_names,
    normalize,
    sort_clubs_by_name,
    sort_clubs_by_size,
)
from models import Club


def test_add_club_creates_object(clubs):
    club = add_club(clubs, "Философский клуб", "Описание", "Модератор")

    assert isinstance(club, Club)
    assert club.id == 1
    assert clubs == [club]


def test_add_club_appends_to_collection(clubs):
    add_club(clubs, "Первый", "Описание", "Модератор")

    add_club(clubs, "Второй", "Описание", "Модератор")

    assert [club.name for club in clubs] == ["Первый", "Второй"]
    assert clubs[1].id == 2


def test_get_club_returns_object(club):
    assert get_club(club, 1).name == "Философский клуб"


def test_get_club_returns_none_when_missing(clubs):
    assert get_club(clubs, 5) is None


def test_find_club_by_name(clubs):
    add_club(clubs, "Философский клуб", "Дебаты", "Айриев")
    add_club(clubs, "Книжный клуб", "Книги", "Смирнова")

    found = find_club(clubs, "книжный")

    assert [item.name for item in found] == ["Книжный клуб"]


def test_find_club_by_description(clubs):
    add_club(clubs, "Философский клуб", "Дебаты", "Айриев")
    add_club(clubs, "Книжный клуб", "Книги", "Смирнова")

    assert len(find_club(clubs, "дебаты")) == 1


def test_find_club_without_result(clubs):
    assert find_club(clubs, "нет такого клуба") == []


def test_iter_club_names_is_generator(clubs):
    add_club(clubs, "Янтарный клуб", "Описание", "Модератор")
    add_club(clubs, "Алые паруса", "Описание", "Модератор")

    names = iter_club_names(clubs)

    assert list(names) == ["Алые паруса", "Янтарный клуб"]


def test_sort_clubs_by_name(clubs):
    add_club(clubs, "Янтарный клуб", "Описание", "Модератор")
    add_club(clubs, "Алые паруса", "Описание", "Модератор")

    assert [item.name for item in sort_clubs_by_name(clubs)] == [
        "Алые паруса", "Янтарный клуб"
    ]


def test_sort_clubs_by_size_descending(clubs):
    first = add_club(clubs, "Первый", "Описание", "Модератор")
    second = add_club(clubs, "Второй", "Описание", "Модератор")

    sizes = {first.id: 1, second.id: 5}

    assert [item.name for item in sort_clubs_by_size(clubs, sizes)] == [
        "Второй", "Первый"
    ]


def test_sort_clubs_by_size_without_counts(clubs):
    add_club(clubs, "Первый", "Описание", "Модератор")
    add_club(clubs, "Второй", "Описание", "Модератор")

    assert len(sort_clubs_by_size(clubs, {})) == 2


def test_get_club_card_uses_object(club):
    card = get_club_card(club[0])

    assert "Философский клуб" in card
    assert "Модератор" in card


def test_normalize_strips_and_lowercases():
    assert normalize("  ФИЛОСОФИЯ ") == "философия"


def test_modules_use_objects_not_dictionaries():
    club = add_club([], "Клуб", "Описание", "Модератор")

    assert not isinstance(club, dict)
    assert club.to_dict()["name"] == "Клуб"
