"""Тесты функций работы с темами дискуссий."""

from models import Topic
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


def test_add_topic_creates_object(topics):
    topic = add_topic(topics, "Справедливость", "средний", ["этика"],
                      "Материалы")

    assert isinstance(topic, Topic)
    assert topic.id == 1
    assert topics == [topic]


def test_add_topic_cleans_tags(topics):
    topic = add_topic(topics, "Тема", "средний", [" этика ", "ЭТИКА"],
                      "Материалы")

    assert list(topic.tags) == ["этика"]


def test_add_topic_appends_to_collection(topics):
    add_topic(topics, "Первая", "средний", [], "Материалы")

    add_topic(topics, "Вторая", "средний", [], "Материалы")

    assert [topic.id for topic in topics] == [1, 2]


def test_get_topic_returns_object(topics):
    add_topic(topics, "Тема", "средний", [], "Материалы")

    assert get_topic(topics, 1).title == "Тема"


def test_get_topic_returns_none_when_missing(topics):
    assert get_topic(topics, 7) is None


def test_find_topics_by_tag_ignores_case(topics):
    add_topic(topics, "Первая", "средний", ["ИИ"], "Материалы")
    add_topic(topics, "Вторая", "средний", ["логика"], "Материалы")

    found = find_topics_by_tag(topics, "ии")

    assert [topic.title for topic in found] == ["Первая"]


def test_find_topics_by_tag_without_result(topics):
    add_topic(topics, "Первая", "средний", ["ИИ"], "Материалы")

    assert find_topics_by_tag(topics, "этика") == []


def test_filter_topics_by_level_is_generator(topics):
    add_topic(topics, "Первая", "средний", [], "Материалы")
    add_topic(topics, "Вторая", "средний", [], "Материалы")
    add_topic(topics, "Третья", "начинающий", [], "Материалы")

    found = filter_topics_by_level(topics, "средний")

    assert len(list(found)) == 2


def test_filter_topics_by_level_without_result(topics):
    add_topic(topics, "Первая", "средний", [], "Материалы")

    assert list(filter_topics_by_level(topics, "продвинутый")) == []


def test_sort_topics_by_level(topics):
    add_topic(topics, "Третья", "продвинутый", [], "Материалы")
    add_topic(topics, "Первая", "начинающий", [], "Материалы")
    add_topic(topics, "Вторая", "средний", [], "Материалы")

    assert [topic.level for topic in sort_topics_by_level(topics)] == [
        "начинающий", "средний", "продвинутый"
    ]


def test_levels_constant_and_order():
    assert LEVELS == ("начинающий", "средний", "продвинутый")
    assert LEVEL_ORDER["средний"] == 1


def test_get_topic_card_uses_object(topic):
    card = get_topic_card(topic[0])

    assert "Тема дискуссии" in card
    assert "этика" in card


def test_modules_use_objects_not_dictionaries(topics):
    added = add_topic(topics, "Тема", "средний", [], "Материалы")

    assert not isinstance(added, dict)
    assert added.to_dict()["title"] == "Тема"
