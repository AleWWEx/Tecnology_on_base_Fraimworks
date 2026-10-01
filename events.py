"""Работа с мероприятиями дискуссионных клубов.

Мероприятия представлены объектами класса models.event.Event, а
коллекция мероприятий — это список объектов List[Event].

Модуль содержит функции, перенесённые из начального сценария ПР1
(get_event_status, get_free_places, get_event_card). Логика ПР1
сохранена, но данные берутся из объектов, а не из отдельных словарей.

Распределение ответственности между объектом и модулем:

- поведение отдельного мероприятия хранится в методах Event
  (status_on, free_places, is_available, check_requirements);
- функции модуля работают с коллекцией: ищут мероприятия, считают
  регистрации и формируют сводные значения.
"""

import datetime
from typing import Iterator, List, Optional, Tuple

from models import (
    EVENT_FORMATS,
    PLACEHOLDING_STATUSES,
    STATUS_ATTENDED,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_FINISHED,
    STATUS_PENDING,
    STATUS_PLANNED,
    STATUS_RUNNING,
    Event,
    calculate_event_status,
    count_free_places,
)
from models.club import Club
from models.registration import Registration
from models.topic import Topic
from utils import next_id

__all__ = [
    "EVENT_FORMATS",
    "PLACEHOLDING_STATUSES",
    "STATUS_ATTENDED",
    "STATUS_CANCELLED",
    "STATUS_CONFIRMED",
    "STATUS_FINISHED",
    "STATUS_PENDING",
    "STATUS_PLANNED",
    "STATUS_RUNNING",
    "add_event",
    "count_active_registrations",
    "count_registrations_by_status",
    "find_events_by_club",
    "get_event",
    "get_event_card",
    "get_event_places",
    "get_event_status",
    "get_free_places",
    "is_event_full",
    "iter_upcoming_events",
    "sort_events_by_date",
]


def add_event(events: List[Event], club_id: int, topic_id: int,
              event_date: datetime.date, start_time: str,
              event_format: str, place: str, capacity: int,
              min_age: int, required_level: str) -> Event:
    """Создать объект мероприятия и добавить его в коллекцию.

    Возвращает созданный объект Event. Если club_id или topic_id не
    соответствуют существующим объектам, ссылки club и topic
    остаются пустыми: их связывает модуль storage.py при загрузке.
    """
    event = Event(
        event_id=next_id(item.id for item in events),
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
    events.append(event)
    return event


def get_event(events: List[Event], event_id: int) -> Optional[Event]:
    """Вернуть объект мероприятия по идентификатору или None."""
    for event in events:
        if event.id == event_id:
            return event
    return None


def get_event_status(event_date: datetime.date,
                     today: Optional[datetime.date] = None) -> str:
    """Определить статус мероприятия по дате его проведения.

    Если дата не передана, используется текущая дата. Функция ПР1
    сохранена: расчёт вынесен в models.event.calculate_event_status,
    чтобы объекты и функции давали одинаковый результат.
    """
    return calculate_event_status(event_date, today)


def get_free_places(current_participants: int, capacity: int) -> int:
    """Вернуть число свободных мест, не меньшее нуля.

    Функция ПР1 сохранена. Тот же расчёт выполняет метод
    Event.free_places() для конкретного мероприятия.
    """
    return count_free_places(current_participants, capacity)


def is_event_full(current_participants: int, capacity: int) -> bool:
    """Проверить, заняты ли все места на мероприятии."""
    return current_participants >= capacity


def find_events_by_club(events: List[Event], club_id: int) -> List[Event]:
    """Найти все мероприятия заданного клуба."""
    return [event for event in events if event.club_id == club_id]


def iter_upcoming_events(events: List[Event],
                         today: datetime.date) -> Iterator[Event]:
    """Генератор: выдавать мероприятия, которые ещё не завершились.

    Мероприятия перебираются в порядке даты: так ближайшие встречи
    оказываются первыми.
    """
    for event in sort_events_by_date(events):
        if event.event_date >= today:
            yield event


def sort_events_by_date(events: List[Event]) -> List[Event]:
    """Отсортировать мероприятия по дате проведения."""
    return sorted(events, key=lambda event: (event.event_date,
                                             event.start_time))


def get_event_places(events: List[Event], event_id: int,
                     current_participants: int) -> Tuple[int, int]:
    """Вернуть пару «число участников, вместимость» для мероприятия.

    Отсутствующее мероприятие приводит к паре из нулей: вызывающий код
    получает безопасное значение вместо исключения. Число участников
    передаётся отдельно: подсчётом регистраций занимается модуль
    registrations.py.
    """
    event = get_event(events, event_id)
    if event is None:
        return 0, 0
    return current_participants, event.capacity


def count_active_registrations(registrations: List[Registration],
                               event_id: int) -> int:
    """Посчитать регистрации мероприятия, которые занимают место.

    Место занимают только подтверждённые заявки и отметки о посещении.
    Заявки, ожидающие подтверждения, образуют лист ожидания и места не
    занимают; отменённые заявки освобождают место. Признак занятия
    места хранится в объекте регистрации: Registration.occupies_place.
    """
    return sum(
        1
        for registration in registrations
        if registration.event_id == event_id
        and registration.occupies_place
    )


def count_registrations_by_status(registrations: List[Registration],
                                  event_id: int, status: str) -> int:
    """Посчитать регистрации мероприятия с заданным статусом."""
    return sum(
        1
        for registration in registrations
        if registration.event_id == event_id
        and registration.status == status
    )


def get_event_card(event: Event, club: Optional[Club],
                   topic: Optional[Topic], current_participants: int,
                   event_status: str) -> str:
    """Сформировать текстовую карточку мероприятия для вывода.

    В отличие от сценария ПР1 карточка собирается методом объекта
    Event.render(): данные клуба и темы берутся из связанных объектов,
    а club и topic передаются для случая, когда связь ещё не
    установлена.
    """
    event.link(club=club, topic=topic)
    return event.render({
        "participants": current_participants,
        "status": event_status,
    })
