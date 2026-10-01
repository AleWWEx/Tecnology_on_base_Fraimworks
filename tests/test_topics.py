"""Тесты функций работы с темами дискуссий."""

import pytest

from topics import (
    LEVEL_ORDER,
    LEVELS,
    add_topic,
    filter_topics_by_level,
    find_topics_by_tag,
    get_topic,
    get_topic_card,
    sort_topics_by_level,
)


def test_add_topic_puts_topic_into_dict():
    topics = {}

    topic_id = add_topic(topics, "Тема", "средний", ["этика"], "Материалы")

    assert len(topics) == 1
    assert topics[topic_id]["title"] == "Тема"


def test_add_topic_removes_duplicate_tags():
    topics = {}

    topic_id = add_topic(
        topics, "Тема", "средний", ["этика", "Этика", "социология"],
        "Материалы",
    )

    assert topics[topic_id]["tags"] == ["этика", "социология"]


def test_get_topic_returns_none_for_unknown_id(topics):
    add_topic(topics, "Тема", "средний", ["этика"], "Материалы")

    assert get_topic(topics, 7) is None


def test_find_topics_by_tag_ignores_case(topics):
    add_topic(topics, "Тема", "средний", ["Этика"], "Материалы")

    assert find_topics_by_tag(topics, "этика") == [1]


def test_find_topics_by_tag_returns_empty_list(topic):
    assert find_topics_by_tag(topic, "кино") == []


def test_filter_topics_by_level_returns_generator(topic):
    result = filter_topics_by_level(topic, "средний")

    assert list(result) == [1]


def test_filter_topics_by_level_skips_other_levels(topics):
    add_topic(topics, "Первая", "начинающий", ["философия"], "Материалы")
    add_topic(topics, "Вторая", "средний", ["этика"], "Материалы")

    assert list(filter_topics_by_level(topics, "начинающий")) == [1]


def test_sort_topics_by_level_orders_from_simple_to_hard(topics):
    add_topic(topics, "Сложная", "продвинутый", ["этика"], "Материалы")
    add_topic(topics, "Простая", "начинающий", ["философия"], "Материалы")
    add_topic(topics, "Средняя", "средний", ["книги"], "Материалы")

    assert sort_topics_by_level(topics) == [2, 3, 1]


def test_level_order_matches_levels_tuple():
    assert list(LEVEL_ORDER) == list(LEVELS)


def test_get_topic_card_contains_tags(topic):
    card = get_topic_card(get_topic(topic, 1))

    assert "Тема дискуссии" in card
    assert "этика" in card


@pytest.mark.parametrize("level", LEVELS)
def test_level_is_known(level):
    assert level in LEVEL_ORDER
