"""Аналитика проекта: сводные данные по мероприятиям и участникам.

Модуль собирает функции, которые обрабатывают коллекции объектов
целиком и возвращают сводные значения: единственное мероприятие или
одна заявка для такой функции не подходят.

Расчёты выполняются по атрибутам и методам объектов: например, число
занятых мест берётся из метода Event.free_places(), а признак
активной заявки — из свойства Registration.is_active.
"""

from typing import Dict, List, Tuple

from events import (
    STATUS_ATTENDED,
    STATUS_CANCELLED,
    STATUS_PENDING,
    count_active_registrations,
    count_registrations_by_status,
)
from models import Event, Registration, Topic
from topics import LEVELS


def get_event_statistics(events: List[Event],
                         registrations: List[Registration]) -> Dict[int, Dict]:
    """Собрать сводку по каждому мероприятию.

    Для каждого мероприятия вычисляются вместимость, число занятых
    мест, число заявок в листе ожидания, число посещений и доля
    заполненности в процентах. Ключом словаря остаётся идентификатор
    мероприятия: по нему удобно обращаться к объекту Event.
    """
    summary: Dict[int, Dict] = {}
    for event in events:
        capacity = event.capacity
        signed_up = count_active_registrations(registrations, event.id)
        summary[event.id] = {
            "capacity": capacity,
            "signed_up": signed_up,
            "free_places": event.free_places(signed_up),
            "waiting": count_registrations_by_status(
                registrations, event.id, STATUS_PENDING
            ),
            "attended": count_registrations_by_status(
                registrations, event.id, STATUS_ATTENDED
            ),
            "cancelled": count_registrations_by_status(
                registrations, event.id, STATUS_CANCELLED
            ),
            "fill_percent": percent(signed_up, capacity),
        }
    return summary


def get_club_event_counts(events: List[Event]) -> Dict[int, int]:
    """Посчитать число мероприятий каждого клуба.

    Клубы без мероприятий в словарь не попадают: их счётчик равен нулю
    и при обращении возвращается значением по умолчанию.
    """
    counts: Dict[int, int] = {}
    for event in events:
        club_id = event.club_id
        counts[club_id] = counts.get(club_id, 0) + 1
    return counts


def count_topics_by_level(topics: List[Topic]) -> Dict[str, int]:
    """Посчитать число тем дискуссий по уровню сложности.

    В результате присутствуют все уровни, включая уровни без тем: иначе
    в отчёте появляются пропуски в строках таблицы.
    """
    counts = {level: 0 for level in LEVELS}
    for topic in topics:
        counts[topic.level] = counts.get(topic.level, 0) + 1
    return counts


def get_top_participants(registrations: List[Registration],
                         limit: int = 5) -> List[Tuple[str, int]]:
    """Получить самых активных участников.

    Возвращает пары «имя, число регистраций», отсортированные по
    убыванию активности. Отменённые заявки не учитываются: о них
    сообщает свойство Registration.is_active.
    """
    counter: Dict[str, int] = {}
    for registration in registrations:
        if not registration.is_active:
            continue
        name = registration.name
        counter[name] = counter.get(name, 0) + 1
    ranked = sorted(counter.items(), key=lambda pair: pair[1], reverse=True)
    return ranked[:limit]


def percent(part: int, whole: int) -> int:
    """Вернуть долю part от whole в процентах, округлённую вниз.

    Нулевой знаменатель трактуется как отсутствие данных: результатом
    является ноль, а не ошибка деления.
    """
    if whole <= 0:
        return 0
    return part * 100 // whole


def format_event_statistics(title: str, events: List[Event],
                            summary: Dict[int, Dict]) -> str:
    """Оформить сводку по мероприятиям в виде таблицы."""
    lines = [title, "-" * len(title)]
    header = (
        f"{'ID':>3} {'Дата':>10} {'Мест':>5} {'Занято':>7} "
        f"{'Свободно':>8} {'Заполнено':>10}"
    )
    lines.append(header)
    for event in sorted(events, key=lambda item: item.id):
        row = summary.get(event.id)
        if row is None:
            continue
        lines.append(
            f"{event.id:>3} "
            f"{event.event_date.strftime('%d.%m.%Y'):>10} "
            f"{row['capacity']:>5} "
            f"{row['signed_up']:>7} "
            f"{row['free_places']:>8} "
            f"{str(row['fill_percent']) + '%':>10}"
        )
    return "\n".join(lines)


def format_topics_by_level(counts: Dict[str, int]) -> str:
    """Оформить число тем по уровням сложности в виде таблицы."""
    lines = ["Темы по уровням сложности", "-" * 25]
    for level, count in counts.items():
        lines.append(f"{level:<14} — {count}")
    return "\n".join(lines)


def describe_entities(entities: List) -> List[str]:
    """Собрать строковые представления объектов разных классов.

    Функция принимает коллекцию объектов Club, Topic, Event или
    Registration и вызывает у каждого метод __str__. Полиморфизм:
    одинаковый вызов даёт разный результат в зависимости от класса
    объекта.
    """
    return [str(entity) for entity in entities]
