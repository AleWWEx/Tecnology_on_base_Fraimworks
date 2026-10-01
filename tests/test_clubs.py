"""Тесты функций работы с клубами."""

from clubs import (
    add_club,
    find_club,
    get_club,
    get_club_card,
    iter_club_names,
    sort_club_ids_by_name,
    sort_club_ids_by_size,
)


def test_add_club_puts_club_into_dict():
    clubs = {}

    club_id = add_club(clubs, "Философский клуб", "Описание", "Модератор")

    assert len(clubs) == 1
    assert clubs[club_id]["name"] == "Философский клуб"
    assert clubs[club_id]["moderator"] == "Модератор"


def test_add_club_generates_increasing_ids(clubs):
    first_id = add_club(clubs, "Первый", "Описание", "Модератор")
    second_id = add_club(clubs, "Второй", "Описание", "Модератор")

    assert first_id == 1
    assert second_id == 2


def test_get_club_returns_data(club):
    assert get_club(club, 1)["name"] == "Философский клуб"


def test_get_club_returns_none_for_unknown_id(club):
    assert get_club(club, 99) is None


def test_find_club_ignores_case(clubs):
    add_club(clubs, "Философский клуб", "Дебаты", "Модератор")

    assert find_club(clubs, "ФИЛОСОФСКИЙ") == [1]


def test_find_club_searches_description(clubs):
    add_club(clubs, "Клуб дебатов", "Британская система", "Модератор")

    assert find_club(clubs, "британская") == [1]


def test_find_club_returns_empty_list(club):
    assert find_club(club, "несуществующий") == []


def test_iter_club_names_yields_sorted_names(clubs):
    add_club(clubs, "Ярмарка", "Описание", "Модератор")
    add_club(clubs, "Абвер", "Описание", "Модератор")

    assert list(iter_club_names(clubs)) == ["Абвер", "Ярмарка"]


def test_sort_club_ids_by_name(clubs):
    add_club(clubs, "Ярмарка", "Описание", "Модератор")
    add_club(clubs, "Абвер", "Описание", "Модератор")

    assert sort_club_ids_by_name(clubs) == [2, 1]


def test_sort_club_ids_by_size_descending(clubs):
    add_club(clubs, "Первый", "Описание", "Модератор")
    add_club(clubs, "Второй", "Описание", "Модератор")

    sizes = {1: 1, 2: 5}

    assert sort_club_ids_by_size(clubs, sizes) == [2, 1]


def test_sort_club_ids_by_size_of_club_without_events(clubs):
    add_club(clubs, "Первый", "Описание", "Модератор")

    assert sort_club_ids_by_size(clubs, {}) == [1]


def test_get_club_card_contains_data(club):
    card = get_club_card(get_club(club, 1))

    assert "Философский клуб" in card
    assert "Модератор" in card
