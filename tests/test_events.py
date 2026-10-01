"""Тесты функций и методов работы с мероприятиями."""

import datetime

from events import (
    EVENT_FORMATS,
    STATUS_ATTENDED,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_FINISHED,
    STATUS_PENDING,
    STATUS_PLANNED,
    STATUS_RUNNING,
    add_event,
    count_active_registrations,
    count_registrations_by_status,
    find_events_by_club,
    get_event,
    get_event_card,
    get_event_places,
    get_event_status,
    get_free_places,
    is_event_full,
    iter_upcoming_events,
    sort_events_by_date,
)
from models import Event


def make_registration(event_id=1, status=STATUS_CONFIRMED):
    """Создать объект регистрации для подсчёта."""
    from models import Registration

    return Registration(
        registration_id=1,
        event_id=event_id,
        name="Участник",
        age=19,
        level="средний",
        has_read_materials=True,
        status=status,
    )


def test_add_event_creates_object(events, club, topic):
    event = add_event(
        events, 1, 1, datetime.date(2026, 10, 15), "18:30", "онлайн",
        "ссылка на комнату", 25, 16, "средний",
    )

    assert isinstance(event, Event)
    assert event.id == 1
    assert event.capacity == 25
    assert event.event_date.year == 2026
    assert events == [event]


def test_add_event_keeps_links_empty(events):
    event = add_event(
        events, 1, 1, datetime.date(2026, 10, 15), "18:30", "онлайн",
        "ссылка", 25, 16, "средний",
    )

    assert event.club is None
    assert event.topic is None


def test_get_event_returns_object(event):
    assert get_event(event, 1).id == 1


def test_get_event_returns_none_when_missing(events):
    assert get_event(events, 5) is None


def test_get_event_status_before_date():
    today = datetime.date(2026, 10, 1)
    future = datetime.date(2026, 10, 15)

    assert get_event_status(future, today) == STATUS_PLANNED


def test_get_event_status_on_date():
    date = datetime.date(2026, 10, 1)

    assert get_event_status(date, date) == STATUS_RUNNING


def test_get_event_status_after_date():
    today = datetime.date(2026, 10, 2)
    past = datetime.date(2026, 10, 1)

    assert get_event_status(past, today) == STATUS_FINISHED


def test_get_event_status_uses_today_if_not_given(monkeypatch):
    fixed_today = datetime.date(2026, 10, 1)
    fake_date = type(
        "FakeDate", (datetime.date,),
        {"today": staticmethod(lambda: fixed_today)},
    )
    monkeypatch.setattr("models.event.datetime.date", fake_date)

    assert get_event_status(fake_date(2026, 10, 2)) == STATUS_PLANNED


def test_get_free_places_never_negative():
    assert get_free_places(23, 25) == 2
    assert get_free_places(25, 25) == 0
    assert get_free_places(30, 25) == 0


def test_is_event_full_returns_true_when_full():
    assert is_event_full(25, 25) is True
    assert is_event_full(23, 25) is False


def test_event_formats_include_offline():
    assert "онлайн" in EVENT_FORMATS
    assert "офлайн" in EVENT_FORMATS


def test_iter_upcoming_events_filters_finished(events):
    add_event(
        events, 1, 1, datetime.date(2026, 9, 25), "18:30", "онлайн",
        "ссылка", 25, 16, "средний",
    )
    add_event(
        events, 1, 1, datetime.date(2026, 10, 20), "18:30", "онлайн",
        "ссылка", 25, 16, "средний",
    )
    today = datetime.date(2026, 10, 1)

    upcoming = list(iter_upcoming_events(events, today))

    assert [item.id for item in upcoming] == [2]


def test_sort_events_by_date_sorts_chronologically(events):
    add_event(
        events, 1, 1, datetime.date(2026, 11, 1), "18:30", "онлайн",
        "ссылка", 25, 16, "средний",
    )
    add_event(
        events, 1, 1, datetime.date(2026, 9, 25), "18:30", "онлайн",
        "ссылка", 25, 16, "средний",
    )
    add_event(
        events, 1, 1, datetime.date(2026, 10, 15), "19:00", "онлайн",
        "ссылка", 25, 16, "средний",
    )
    add_event(
        events, 1, 1, datetime.date(2026, 10, 15), "18:30", "онлайн",
        "ссылка", 25, 16, "средний",
    )

    assert [item.id for item in sort_events_by_date(events)] == [2, 4, 3, 1]


def test_find_events_by_club(events):
    add_event(
        events, 1, 1, datetime.date(2026, 10, 15), "18:30", "онлайн",
        "ссылка", 25, 16, "средний",
    )
    add_event(
        events, 2, 1, datetime.date(2026, 10, 16), "18:30", "офлайн",
        "Зал", 10, 16, "средний",
    )

    found = find_events_by_club(events, 2)

    assert [item.id for item in found] == [2]


def test_get_event_places_returns_zero_for_missing(events):
    assert get_event_places(events, 99, 10) == (0, 0)


def test_get_event_places_returns_current_and_capacity(event):
    assert get_event_places(event, 1, 23) == (23, 25)


def test_count_active_registrations_considers_statuses():
    registrations = [
        make_registration(1, STATUS_CONFIRMED),
        make_registration(1, STATUS_ATTENDED),
        make_registration(1, STATUS_CANCELLED),
        make_registration(1, STATUS_PENDING),
        make_registration(2, STATUS_CONFIRMED),
    ]

    assert count_active_registrations(registrations, 1) == 2


def test_count_registrations_by_status_counts_exact_status():
    registrations = [
        make_registration(1, STATUS_PENDING),
        make_registration(1, STATUS_PENDING),
        make_registration(2, STATUS_PENDING),
    ]

    assert count_registrations_by_status(
        registrations, 1, STATUS_PENDING
    ) == 2


def test_get_event_card_includes_key_data(event):
    card = get_event_card(event[0], event[0].club, event[0].topic, 23,
                          STATUS_PLANNED)

    assert "Тема дискуссии" in card
    assert "Философский клуб" in card
    assert "свободно 2" in card
    assert STATUS_PLANNED in card


def test_get_event_card_links_objects(event):
    target = event[0]
    target.link()

    get_event_card(target, target.club, target.topic, 0, STATUS_PLANNED)

    assert target.club is not None
    assert target.topic is not None


def test_event_methods_match_module_functions(event):
    target = event[0]
    today = datetime.date(2026, 10, 1)

    assert target.status_on(today) == get_event_status(
        target.event_date, today
    )
    assert target.free_places(23) == get_free_places(23, target.capacity)
