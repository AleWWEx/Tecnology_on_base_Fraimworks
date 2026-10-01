"""Тесты функций аналитики и оформления отчётов."""

import datetime

from analytics import (
    count_topics_by_level,
    describe_entities,
    format_event_statistics,
    format_topics_by_level,
    get_club_event_counts,
    get_event_statistics,
    get_top_participants,
    percent,
)
from events import (
    STATUS_ATTENDED,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    add_event,
)
from models import Registration
from registrations import create_registration
from topics import LEVELS, add_topic


def make_registration(event_id=1, name="Участник",
                      status=STATUS_CONFIRMED):
    """Создать объект регистрации для подсчётов."""
    return Registration(
        registration_id=event_id,
        event_id=event_id,
        name=name,
        age=19,
        level="средний",
        has_read_materials=True,
        status=status,
    )


def make_events():
    """Вернуть список из двух мероприятий разных клубов."""
    events = []
    add_event(
        events, 1, 1, datetime.date(2026, 10, 15), "18:30", "онлайн",
        "ссылка", 25, 16, "средний",
    )
    add_event(
        events, 2, 2, datetime.date(2026, 11, 1), "19:00", "офлайн",
        "Зал клуба", 10, 18, "продвинутый",
    )
    return events


def test_get_event_statistics_counts_places():
    events = make_events()
    registrations = [
        make_registration(1, status=STATUS_CONFIRMED),
        make_registration(1, status=STATUS_CONFIRMED),
        make_registration(1, status=STATUS_PENDING),
        make_registration(1, status=STATUS_CANCELLED),
        make_registration(2, status=STATUS_ATTENDED),
    ]

    summary = get_event_statistics(events, registrations)

    assert summary[1]["capacity"] == 25
    assert summary[1]["signed_up"] == 2
    assert summary[1]["free_places"] == 23
    assert summary[1]["waiting"] == 1
    assert summary[1]["attended"] == 0
    assert summary[1]["cancelled"] == 1
    assert summary[1]["fill_percent"] == 8
    assert summary[2]["attended"] == 1


def test_get_event_statistics_with_no_data():
    summary = get_event_statistics(make_events(), [])

    assert summary[1]["signed_up"] == 0
    assert summary[1]["fill_percent"] == 0


def test_get_club_event_counts():
    counts = get_club_event_counts(make_events())

    assert counts == {1: 1, 2: 1}


def test_get_club_event_counts_ignores_empty():
    assert get_club_event_counts([]) == {}


def test_count_topics_by_level():
    topics = []
    add_topic(topics, "Первая", "средний", ["этика"], "Материалы")
    add_topic(topics, "Вторая", "средний", ["логика"], "Материалы")
    add_topic(topics, "Третья", "начинающий", ["этика"], "Материалы")

    counts = count_topics_by_level(topics)

    assert counts["средний"] == 2
    assert counts["начинающий"] == 1
    assert counts["продвинутый"] == 0
    assert list(counts) == list(LEVELS)


def test_get_top_participants_ignores_cancelled():
    registrations = []
    create_registration(
        registrations, 1, "Мария К.", 19, "средний", True, STATUS_CONFIRMED
    )
    create_registration(
        registrations, 2, "Мария К.", 19, "средний", True, STATUS_PENDING
    )
    create_registration(
        registrations, 3, "Мария К.", 19, "средний", True, STATUS_CANCELLED
    )
    create_registration(
        registrations, 1, "Ольга П.", 19, "средний", True, STATUS_CONFIRMED
    )

    ranked = get_top_participants(registrations)

    assert ranked == [("Мария К.", 2), ("Ольга П.", 1)]


def test_get_top_participants_respects_limit():
    registrations = [
        make_registration(1, name="Участник"),
        make_registration(2, name="Другой"),
    ]

    assert len(get_top_participants(registrations, limit=1)) == 1


def test_percent_rounds_down():
    assert percent(1, 3) == 33
    assert percent(25, 25) == 100
    assert percent(0, 10) == 0


def test_percent_handles_zero_whole():
    assert percent(5, 0) == 0


def test_format_event_statistics_contains_rows():
    events = make_events()
    summary = get_event_statistics(events, [])

    table = format_event_statistics("Заполненность", events, summary)

    assert "Заполненность" in table
    assert "15.10.2026" in table
    assert "01.11.2026" in table
    assert "0%" in table


def test_format_event_statistics_skips_unknown_event():
    events = make_events()
    summary = get_event_statistics(events, [])
    summary[99] = summary[1]

    table = format_event_statistics("Заполненность", events, summary)

    assert "  99" not in table


def test_format_topics_by_level():
    counts = {level: 0 for level in LEVELS}

    table = format_topics_by_level(counts)

    for level in LEVELS:
        assert level in table


def test_describe_entities_uses_polymorphic_str(event, topic,
                                                registrations_of_event):
    objects = [event[0], topic[0], registrations_of_event[0]]

    texts = describe_entities(objects)

    assert texts[0].startswith("Мероприятие")
    assert texts[1].startswith("Тема")
    assert texts[2].startswith("Регистрация")
