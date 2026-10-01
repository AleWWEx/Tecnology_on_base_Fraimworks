"""Работа с мероприятиями дискуссионных клубов.

Мероприятия хранятся в словаре events: ключ — идентификатор
мероприятия, значение — словарь с данными (клуб, тема, дата, начало,
формат, место, вместимость, требования к участнику).

Модуль содержит функции, перенесённые из начального сценария ПР1
(get_event_status, get_free_places, get_event_card). Логика ПР1 сохранена,
но данные берутся из коллекций проекта, а не из отдельных переменных.
"""

import datetime
from typing import Iterator, Optional

from utils import format_date, next_id

STATUS_PLANNED = "планируется"
STATUS_RUNNING = "идёт"
STATUS_FINISHED = "завершено"

STATUS_PENDING = "ожидает подтверждения"
STATUS_CONFIRMED = "подтверждён"
STATUS_ATTENDED = "присутствовал"
STATUS_CANCELLED = "отменён"

PLACEHOLDING_STATUSES = (STATUS_CONFIRMED, STATUS_ATTENDED)

EVENT_FORMATS = ("онлайн", "офлайн")


def add_event(events: dict[int, dict], club_id: int, topic_id: int,
              event_date: datetime.date, start_time: str,
              event_format: str, place: str, capacity: int,
              min_age: int, required_level: str) -> int:
    """Добавить мероприятие в словарь events.

    Идентификатор записывается и в ключ словаря, и в данные
    мероприятия: без него запись нельзя сохранить в JSON-файл и
    прочитать обратно. Дата сохраняется в виде объекта date:
    преобразование строк выполняется в модуле storage.py.
    Возвращает идентификатор созданного мероприятия.
    """
    event_id = next_id(events)
    events[event_id] = {
        "id": event_id,
        "club_id": club_id,
        "topic_id": topic_id,
        "event_date": event_date,
        "start_time": start_time,
        "format": event_format,
        "place": place,
        "capacity": capacity,
        "min_age": min_age,
        "required_level": required_level,
    }
    return event_id


def get_event(events: dict[int, dict], event_id: int) -> Optional[dict]:
    """Вернуть данные мероприятия по идентификатору или None."""
    return events.get(event_id)


def get_event_status(event_date: datetime.date,
                     today: Optional[datetime.date] = None) -> str:
    """Определить статус мероприятия по дате его проведения.

    Если дата не передана, используется текущая дата.
    """
    if today is None:
        today = datetime.date.today()
    if event_date < today:
        return STATUS_FINISHED
    if event_date == today:
        return STATUS_RUNNING
    return STATUS_PLANNED


def get_free_places(current_participants: int, capacity: int) -> int:
    """Вернуть число свободных мест, не меньшее нуля."""
    free_places = capacity - current_participants
    if free_places < 0:
        return 0
    return free_places


def is_event_full(current_participants: int, capacity: int) -> bool:
    """Проверить, заняты ли все места на мероприятии."""
    return current_participants >= capacity


def find_events_by_club(events: dict[int, dict], club_id: int) -> list[int]:
    """Найти все мероприятия заданного клуба."""
    return [
        event_id
        for event_id, event in events.items()
        if event["club_id"] == club_id
    ]


def iter_upcoming_events(events: dict[int, dict],
                         today: datetime.date) -> Iterator[int]:
    """Генератор: выдавать мероприятия, которые ещё не завершились.

    Мероприятия перебираются в порядке даты: так ближайшие встречи
    оказываются первыми.
    """
    for event_id in sort_events_by_date(events):
        if events[event_id]["event_date"] >= today:
            yield event_id


def sort_events_by_date(events: dict[int, dict]) -> list[int]:
    """Отсортировать мероприятия по дате проведения."""
    return sorted(
        events,
        key=lambda event_id: (events[event_id]["event_date"],
                              events[event_id]["start_time"]),
    )


def get_event_places(events: dict[int, dict], event_id: int,
                     current_participants: int) -> tuple[int, int]:
    """Вернуть пару «число участников, вместимость» для мероприятия.

    Отсутствующее мероприятие приводит к паре из нулей: вызывающий код
    получает безопасное значение вместо исключения. Число участников
    передаётся отдельно: подсчётом регистраций занимается модуль
    registrations.py.
    """
    event = get_event(events, event_id)
    if event is None:
        return 0, 0
    return current_participants, int(event["capacity"])


def count_active_registrations(registrations: list[dict],
                               event_id: int) -> int:
    """Посчитать регистрации мероприятия, которые занимают место.

    Место занимают только подтверждённые заявки и отметки о посещении.
    Заявки, ожидающие подтверждения, образуют лист ожидания и места не
    занимают; отменённые заявки освобождают место.
    """
    return sum(
        1
        for record in registrations
        if record["event_id"] == event_id
        and record["status"] in PLACEHOLDING_STATUSES
    )


def count_registrations_by_status(registrations: list[dict], event_id: int,
                                  status: str) -> int:
    """Посчитать регистрации мероприятия с заданным статусом."""
    return sum(
        1
        for record in registrations
        if record["event_id"] == event_id
        and record["status"] == status
    )


def resolve_event_data(event: dict) -> dict:
    """Вернуть данные одного мероприятия.

    Помимо обычного вызова, когда передаются данные мероприятия,
    поддерживается форма сценария ПР1: словарь, где мероприятие хранится
    под идентификатором 1.
    """
    if "capacity" in event:
        return event
    if 1 in event:
        return event[1]
    return event


def get_event_card(event: dict, club: dict, topic: dict,
                   current_participants: int,
                   event_status: str) -> str:
    """Сформировать текстовую карточку мероприятия для вывода.

    В отличие от сценария ПР1 карточка собирается из данных коллекций
    проекта: карточки клубов и тем приходят аргументами.
    """
    event_data = resolve_event_data(event)
    capacity = int(event_data["capacity"])
    free_places = get_free_places(current_participants, capacity)
    return (
        f"Клуб: {club['name']}\n"
        f"Тема: {topic['title']}\n"
        f"Уровень темы: {topic['level']}\n"
        f"Дата: {format_date(event_data['event_date'])}, начало в "
        f"{event_data['start_time']}\n"
        f"Формат: {event_data['format']} ({event_data['place']})\n"
        f"Требования: возраст {event_data['min_age']}+, уровень "
        f"«{event_data['required_level']}», рекомендованные материалы "
        "прочитаны\n"
        f"Места: занято {current_participants} из {event_data['capacity']}, "
        f"свободно {free_places}\n"
        f"Статус мероприятия: {event_status}"
    )
