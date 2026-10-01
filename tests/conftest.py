"""Общие фикстуры для тестов проекта.

Фикстуры создают небольшие коллекции объектов, на которых проверяются
классы и функции модулей. Каталог данных проекта подменяется временным:
тесты не изменяют файлы репозитория.
"""

import datetime

import pytest

import storage
from clubs import add_club
from events import STATUS_CONFIRMED, add_event
from models import Club, Event, Registration, Topic
from registrations import create_registration
from topics import add_topic


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Подменить каталог данных проекта временным каталогом."""
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def clubs():
    """Пустой список клубов: List[Club]."""
    return []


@pytest.fixture
def topics():
    """Пустой список тем дискуссий: List[Topic]."""
    return []


@pytest.fixture
def events():
    """Пустой список мероприятий: List[Event]."""
    return []


@pytest.fixture
def registrations():
    """Пустой список регистраций: List[Registration]."""
    return []


@pytest.fixture
def club(clubs):
    """Список клубов с одним объектом Club."""
    add_club(clubs, "Философский клуб", "Описание клуба", "Модератор")
    return clubs


@pytest.fixture
def topic(topics):
    """Список тем с одним объектом Topic среднего уровня."""
    add_topic(topics, "Тема дискуссии", "средний", ["этика"], "Материалы")
    return topics


@pytest.fixture
def event(events, club, topic):
    """Список мероприятий с одним объектом Event на 25 мест."""
    added = add_event(
        events, 1, 1, datetime.date(2026, 10, 15), "18:30", "онлайн",
        "ссылка на комнату", 25, 16, "средний",
    )
    added.link(club=club[0], topic=topic[0])
    return events


@pytest.fixture
def registrations_of_event(registrations, event):
    """Список из 23 подтверждённых регистраций на первое мероприятие."""
    for number in range(23):
        registration = create_registration(
            registrations, 1, f"Участник {number}", 19, "средний", True,
            STATUS_CONFIRMED,
        )
        registration.link(event[0])
    return registrations


@pytest.fixture
def answers(monkeypatch):
    """Подменить ввод пользователя заранее заданными ответами.

    Возвращает функцию, которой передаётся список ответов. Ответы
    выдаются по порядку; по исчерпании списка возвращается пустая
    строка.
    """
    queue: list[str] = []

    def set_answers(values):
        queue.clear()
        queue.extend(values)

    def fake_input(prompt=""):
        print(prompt, end="")
        if queue:
            answer = queue.pop(0)
        else:
            answer = ""
        print(answer)
        return answer

    monkeypatch.setattr("builtins.input", fake_input)
    return set_answers


@pytest.fixture
def make_club():
    """Фабрика объектов Club для тестов классов."""

    def factory(club_id=1, name="Клуб", description="Описание",
                moderator="Модератор"):
        return Club(
            club_id=club_id,
            name=name,
            description=description,
            moderator=moderator,
        )

    return factory


@pytest.fixture
def make_topic():
    """Фабрика объектов Topic для тестов классов."""

    def factory(topic_id=1, title="Тема", level="средний", tags=None,
                materials="Материалы"):
        return Topic(
            topic_id=topic_id,
            title=title,
            level=level,
            tags=tags if tags is not None else ["этика"],
            materials=materials,
        )

    return factory


@pytest.fixture
def make_event(make_club, make_topic):
    """Фабрика объектов Event со связанными клубом и темой."""

    def factory(event_id=1, club_id=1, topic_id=1,
                event_date=datetime.date(2026, 10, 15), start_time="18:30",
                event_format="онлайн", place="ссылка", capacity=25,
                min_age=16, required_level="средний"):
        event = Event(
            event_id=event_id,
            club_id=club_id,
            topic_id=topic_id,
            event_date=event_date,
            start_time=start_time,
            event_format=event_format,
            place=place,
            capacity=capacity,
            min_age=min_age,
            required_level=required_level,
        )
        event.link(club=make_club(club_id), topic=make_topic(topic_id))
        return event

    return factory


@pytest.fixture
def make_registration():
    """Фабрика объектов Registration для тестов классов."""

    def factory(registration_id=1, event_id=1, name="Мария К.", age=19,
                level="средний", has_read_materials=True,
                status="ожидает подтверждения", ticket_code="", event=None):
        return Registration(
            registration_id=registration_id,
            event_id=event_id,
            name=name,
            age=age,
            level=level,
            has_read_materials=has_read_materials,
            status=status,
            ticket_code=ticket_code,
            event=event,
        )

    return factory
