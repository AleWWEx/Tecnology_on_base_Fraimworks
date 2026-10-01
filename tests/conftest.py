"""Общие фикстуры для тестов проекта.

Фикстуры создают небольшие коллекции данных, на которых проверяются
функции модулей. Каталог данных проекта подменяется временным: тесты
не изменяют файлы репозитория.
"""

import datetime

import pytest

import storage
from clubs import add_club
from events import add_event
from registrations import STATUS_CONFIRMED, create_registration
from topics import add_topic


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Подменить каталог данных проекта временным каталогом."""
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    return tmp_path


@pytest.fixture
def clubs():
    """Пустой словарь клубов."""
    return {}


@pytest.fixture
def topics():
    """Пустой словарь тем дискуссий."""
    return {}


@pytest.fixture
def events():
    """Пустой словарь мероприятий."""
    return {}


@pytest.fixture
def registrations():
    """Пустой список регистраций."""
    return []


@pytest.fixture
def club(clubs):
    """Словарь клубов с одним клубом."""
    add_club(clubs, "Философский клуб", "Описание клуба", "Модератор")
    return clubs


@pytest.fixture
def topic(topics):
    """Словарь тем с одной тем среднего уровня."""
    add_topic(topics, "Тема дискуссии", "средний", ["этика"], "Материалы")
    return topics


@pytest.fixture
def event(events):
    """Словарь мероприятий с одним мероприятием на 25 мест."""
    add_event(
        events, 1, 1, datetime.date(2026, 10, 15), "18:30", "онлайн",
        "ссылка на комнату", 25, 16, "средний",
    )
    return events


@pytest.fixture
def registrations_of_event(registrations, event):
    """Список из 23 подтверждённых регистраций на первое мероприятие."""
    for number in range(23):
        create_registration(
            registrations, 1, f"Участник {number}", 19, "средний", True,
            STATUS_CONFIRMED,
        )
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
