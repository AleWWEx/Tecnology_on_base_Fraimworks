"""Тесты классов предметной области.

Проверяются создание объектов, значения атрибутов, строковое
представление, методы классов, наследование, полиморфизм,
инкапсуляция, а также статические методы и методы класса.
"""

import datetime
import inspect

import pytest

from models import BaseEntity, Club, Event, Registration, Topic
from models.event import (
    STATUS_FINISHED,
    STATUS_PLANNED,
    STATUS_RUNNING,
    calculate_event_status,
    check_event_requirements,
    count_free_places,
)
from models.registration import (
    REGISTRATION_STATUSES,
    STATUS_ATTENDED,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
)


def test_club_attributes(make_club):
    club = make_club(3, "Философский клуб", "Описание", "Айриев")

    assert club.id == 3
    assert club.name == "Философский клуб"
    assert club.description == "Описание"
    assert club.moderator == "Айриев"


def test_club_is_instance_of_base_entity(make_club):
    assert isinstance(make_club(), BaseEntity)


def test_club_str_contains_name(make_club):
    club = make_club(name="Философский клуб")

    assert "Философский клуб" in str(club)


def test_club_repr_contains_class_and_id(make_club):
    assert repr(make_club(club_id=7)) == "Club(id=7)"


def test_club_from_data_creates_object():
    club = Club.from_data({
        "id": 2,
        "name": "Книжный клуб",
        "description": "Обсуждение книг",
        "moderator": "Смирнова",
    })

    assert club.id == 2
    assert club.name == "Книжный клуб"
    assert club.moderator == "Смирнова"


def test_club_from_data_uses_keyword_identifier():
    club = Club.from_data({"name": "Клуб"}, club_id=5)

    assert club.id == 5


def test_club_from_data_without_identifier_raises():
    with pytest.raises(ValueError):
        Club.from_data({"name": "Клуб"})


def test_club_to_dict_round_trip(make_club):
    club = make_club()
    data = club.to_dict()

    assert data["id"] == 1
    assert Club.from_data(data).to_dict() == data


def test_club_matches_ignores_case(make_club):
    club = make_club(name="Философский клуб", description="Дебаты")

    assert club.matches("ФИЛОСОФСКИЙ") is True
    assert club.matches("дебаты") is True
    assert club.matches("спорт") is False


def test_club_render_contains_all_fields(make_club):
    club = make_club(moderator="Айриев")

    card = club.render()

    assert "Клуб:" in card
    assert "Айриев" in card
    assert "Мероприятий: 0" in card


def test_club_render_accepts_context(make_club):
    card = make_club().render({"event_count": 3})

    assert "Мероприятий: 3" in card


def test_club_id_can_be_changed(make_club):
    club = make_club()

    club.id = 10

    assert club.id == 10


def test_clubs_are_compared_by_id(make_club):
    assert make_club(club_id=1) == make_club(club_id=1, name="Другой")
    assert make_club(club_id=1) != make_club(club_id=2)


def test_different_classes_are_not_equal(make_club, make_topic):
    assert make_club(club_id=1) != make_topic(topic_id=1)


def test_objects_are_hashable(make_club):
    assert len({make_club(club_id=1), make_club(club_id=1)}) == 1


def test_topic_cleans_tags(make_topic):
    topic = make_topic(tags=[" этика ", "ЭТИКА", "логика", ""])

    assert list(topic.tags) == ["этика", "логика"]


def test_topic_tags_are_immutable_copy(make_topic):
    topic = make_topic(tags=["этика"])

    tags = topic.tags
    tags += ("логика",)

    assert list(topic.tags) == ["этика"]


def test_topic_has_tag(make_topic):
    topic = make_topic(tags=["ИИ", "этика"])

    assert topic.has_tag("ии") is True
    assert topic.has_tag(" этика ") is True
    assert topic.has_tag("логика") is False


def test_topic_has_level(make_topic):
    assert make_topic(level="средний").has_level("СРЕДНИЙ") is True
    assert make_topic(level="средний").has_level("начинающий") is False


def test_topic_to_dict_contains_tags_list(make_topic):
    data = make_topic().to_dict()

    assert data["tags"] == ["этика"]
    assert isinstance(data["tags"], list)


def test_topic_render_contains_tags(make_topic):
    assert "этика" in make_topic().render()


def test_event_attributes(make_event):
    event = make_event(
        event_id=2, capacity=30, min_age=18, required_level="продвинутый"
    )

    assert event.id == 2
    assert event.capacity == 30
    assert event.min_age == 18
    assert event.required_level == "продвинутый"
    assert event.event_date == datetime.date(2026, 10, 15)


def test_event_negative_capacity_raises(make_event):
    event = make_event()

    with pytest.raises(ValueError):
        event.capacity = -1


def test_event_capacity_can_be_changed(make_event):
    event = make_event()

    event.capacity = 40

    assert event.capacity == 40


def test_event_status_on_planned_date(make_event):
    event = make_event(event_date=datetime.date(2026, 10, 15))

    assert event.status_on(datetime.date(2026, 10, 1)) == STATUS_PLANNED


def test_event_status_on_running_date(make_event):
    event = make_event(event_date=datetime.date(2026, 10, 1))

    assert event.status_on(datetime.date(2026, 10, 1)) == STATUS_RUNNING


def test_event_status_on_finished_date(make_event):
    event = make_event(event_date=datetime.date(2026, 9, 1))

    assert event.status_on(datetime.date(2026, 10, 1)) == STATUS_FINISHED


def test_event_status_property_uses_today(make_event):
    event = make_event(event_date=datetime.date(2099, 1, 1))

    assert event.status == STATUS_PLANNED


def test_event_free_places(make_event):
    assert make_event(capacity=25).free_places(23) == 2


def test_event_free_places_never_negative(make_event):
    assert make_event(capacity=25).free_places(30) == 0


def test_event_is_full(make_event):
    assert make_event(capacity=25).is_full(25) is True
    assert make_event(capacity=25).is_full(24) is False


def test_event_is_available(make_event):
    event = make_event(capacity=25)
    today = datetime.date(2026, 10, 1)

    assert event.is_available(23, today) is True
    assert event.is_available(25, today) is False


def test_event_is_not_available_when_finished(make_event):
    event = make_event(event_date=datetime.date(2026, 9, 1))

    assert event.is_available(0, datetime.date(2026, 10, 1)) is False


def test_event_check_requirements_ok(make_event):
    assert make_event().check_requirements(19, "средний", True) == ""


def test_event_check_requirements_age(make_event):
    reason = make_event(min_age=16).check_requirements(14, "средний", True)

    assert "возраст" in reason


def test_event_check_requirements_materials(make_event):
    reason = make_event().check_requirements(19, "средний", False)

    assert "материалы" in reason


def test_event_check_requirements_level(make_event):
    reason = make_event().check_requirements(19, "начинающий", True)

    assert "уровень" in reason


def test_event_link_sets_objects(make_event):
    event = make_event()
    club = make_event().club
    topic = make_event().topic

    event.link(club=club, topic=topic)

    assert event.club is club
    assert event.topic is topic


def test_event_club_name_and_topic_title(make_event):
    event = make_event()

    assert event.club_name() == "Клуб"
    assert event.topic_title() == "Тема"


def test_event_without_links_reports_missed_objects(make_event):
    event = make_event()
    event.club = None
    event.topic = None

    assert event.club_name() == "клуб не найден"
    assert event.topic_title() == "тема не найдена"


def test_event_from_data_parses_date():
    event = Event.from_data({
        "id": 1,
        "club_id": 1,
        "topic_id": 1,
        "event_date": "2026-10-15",
        "start_time": "18:30",
        "format": "онлайн",
        "place": "ссылка",
        "capacity": 25,
        "min_age": 16,
        "required_level": "средний",
    }, parse_date=datetime.date.fromisoformat)

    assert event.event_date == datetime.date(2026, 10, 15)


def test_event_to_dict_stores_iso_date(make_event):
    data = make_event().to_dict()

    assert data["event_date"] == "2026-10-15"


def test_event_to_dict_keeps_only_data(make_event):
    data = make_event().to_dict()

    assert set(data) == {
        "id", "club_id", "topic_id", "event_date", "start_time",
        "format", "place", "capacity", "min_age", "required_level",
    }


def test_event_render_uses_context(make_event):
    event = make_event()

    card = event.render({"participants": 23, "status": STATUS_PLANNED})

    assert "занято 23 из 25" in card
    assert "свободно 2" in card
    assert "Клуб" in card


def test_event_describe_contains_date(make_event):
    assert "15.10.2026" in make_event().describe()


def test_registration_attributes(make_registration):
    registration = make_registration(
        registration_id=4, event_id=2, name="Иван П.", age=17,
        level="начинающий", has_read_materials=False,
    )

    assert registration.id == 4
    assert registration.event_id == 2
    assert registration.name == "Иван П."
    assert registration.age == 17
    assert registration.is_active is True


def test_registration_generates_ticket_code(make_registration):
    registration = make_registration()

    assert registration.ticket_code.startswith("DC-")
    assert len(registration.ticket_code) == 7


def test_registration_keeps_given_ticket_code(make_registration):
    registration = make_registration(ticket_code="DC-0001")

    assert registration.ticket_code == "DC-0001"


def test_registration_unknown_status_raises(make_registration):
    with pytest.raises(ValueError):
        make_registration(status="неизвестный")


def test_registration_status_is_protected(make_registration):
    registration = make_registration(status=STATUS_CONFIRMED)

    with pytest.raises(ValueError):
        registration.status = "выдуманный"


def test_registration_known_status_is_accepted(make_registration):
    registration = make_registration()

    registration.status = STATUS_ATTENDED

    assert registration.status == STATUS_ATTENDED


def test_registration_confirm_changes_state(make_registration):
    registration = make_registration()

    registration.confirm()

    assert registration.status == STATUS_CONFIRMED
    assert registration.confirmed_at != ""


def test_registration_confirm_sets_date(make_registration):
    registration = make_registration()

    registration.confirm(datetime.date(2026, 10, 1))

    assert registration.confirmed_at == "2026-10-01"


def test_registration_confirm_ignores_confirmed(make_registration):
    registration = make_registration(status=STATUS_CONFIRMED)

    registration.confirm()

    assert registration.status == STATUS_CONFIRMED


def test_registration_confirm_ignores_cancelled(make_registration):
    registration = make_registration(status=STATUS_CANCELLED)

    registration.confirm()

    assert registration.status == STATUS_CANCELLED


def test_registration_cancel_changes_state(make_registration):
    registration = make_registration(status=STATUS_CONFIRMED)

    registration.cancel()

    assert registration.status == STATUS_CANCELLED
    assert registration.is_active is False


def test_registration_cancel_clears_confirmation_date(make_registration):
    registration = make_registration(status=STATUS_CONFIRMED)
    registration.confirm(datetime.date(2026, 10, 1))

    registration.cancel()

    assert registration.confirmed_at == ""


def test_registration_occupies_place_only_when_confirmed(
        make_registration):
    assert make_registration().occupies_place is False
    assert make_registration(status=STATUS_PENDING).occupies_place is False
    assert make_registration(
        status=STATUS_CONFIRMED).occupies_place is True
    assert make_registration(
        status=STATUS_ATTENDED).occupies_place is True
    assert make_registration(
        status=STATUS_CANCELLED).occupies_place is False


def test_registration_is_waiting_and_is_cancelled(make_registration):
    waiting = make_registration()

    assert waiting.is_waiting() is True
    assert waiting.is_cancelled() is False

    waiting.cancel()

    assert waiting.is_waiting() is False
    assert waiting.is_cancelled() is True


def test_registration_link_sets_event(make_registration, make_event):
    registration = make_registration()
    event = make_event()

    registration.link(event)

    assert registration.event is event
    assert registration.event_date_text() == "15.10.2026"


def test_registration_without_event_reports_missed_event(make_registration):
    assert make_registration().event_date_text() == "мероприятие не найдено"


def test_registration_from_data(make_registration):
    registration = Registration.from_data({
        "id": 9,
        "event_id": 1,
        "name": "Ольга П.",
        "age": 17,
        "level": "средний",
        "has_read_materials": True,
        "status": STATUS_CONFIRMED,
        "ticket_code": "DC-1111",
    })

    assert registration.id == 9
    assert registration.ticket_code == "DC-1111"
    assert registration.occupies_place is True


def test_registration_to_dict_keeps_event_id(make_registration, make_event):
    registration = make_registration(event=make_event())

    data = registration.to_dict()

    assert data["event_id"] == 1
    assert "event" not in data


def test_registration_render_uses_event_data(make_registration, make_event):
    registration = make_registration(event=make_event())

    card = registration.render()

    assert "Мария К." in card
    assert "15.10.2026" in card
    assert "18:30" in card


def test_registration_describe_contains_status(make_registration):
    text = make_registration(status=STATUS_CONFIRMED).describe()

    assert "подтверждён" in text


def test_generate_ticket_code_is_static_method():
    descriptor = inspect.getattr_static(
        Registration, "generate_ticket_code"
    )

    assert isinstance(descriptor, staticmethod)


def test_generate_ticket_code_generates_new_values():
    codes = {Registration.generate_ticket_code() for _ in range(20)}

    assert len(codes) > 1
    assert all(code.startswith("DC-") for code in codes)


def test_from_data_is_classmethod():
    descriptor = inspect.getattr_static(Registration, "from_data")

    assert isinstance(descriptor, classmethod)


def test_id_property_is_descriptor(make_club):
    assert isinstance(
        inspect.getattr_static(BaseEntity, "id"), property
    )


def test_polymorphic_str_for_all_models(make_club, make_topic, make_event,
                                        make_registration):
    objects = [
        make_club(),
        make_topic(),
        make_event(),
        make_registration(),
    ]

    texts = [str(item) for item in objects]

    assert texts[0].startswith("Клуб")
    assert texts[1].startswith("Тема")
    assert texts[2].startswith("Мероприятие")
    assert texts[3].startswith("Регистрация")


def test_models_share_base_class_attributes():
    for model in (Club, Topic, Event, Registration):
        assert issubclass(model, BaseEntity)
        assert model.KIND != BaseEntity.KIND


def test_base_entity_describe_is_generic():
    entity = BaseEntity(5)

    assert entity.describe() == "сущность 5"
    assert entity.render() == "сущность 5"
    assert entity.to_dict() == {"id": 5}


def test_base_entity_equality_with_other_type(make_club):
    assert make_club() != "не объект"


def test_calculate_event_status_uses_today(monkeypatch):
    fixed = datetime.date(2026, 10, 1)
    fake_date = type(
        "FakeDate", (datetime.date,),
        {"today": staticmethod(lambda: fixed)},
    )
    monkeypatch.setattr(
        "models.event.datetime.date", fake_date
    )

    assert calculate_event_status(fake_date(2026, 10, 15)) == STATUS_PLANNED


def test_count_free_places_function():
    assert count_free_places(23, 25) == 2
    assert count_free_places(30, 25) == 0


def test_check_event_requirements_function():
    assert check_event_requirements(19, "средний", True, 16, "средний") == ""
    assert "возраст" in check_event_requirements(
        10, "средний", True, 16, "средний"
    )


def test_registration_statuses_constant():
    assert STATUS_PENDING in REGISTRATION_STATUSES
    assert STATUS_CANCELLED in REGISTRATION_STATUSES
