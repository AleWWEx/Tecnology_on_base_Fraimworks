"""Аналитика проекта: сводные данные по мероприятиям и участникам.

Модуль собирает функции, которые обрабатывают коллекции проекта целиком
и возвращают сводные значения. Такие функции используют циклы для
накопления результата.
"""

from events import (
    STATUS_ATTENDED,
    STATUS_CANCELLED,
    STATUS_PENDING,
    count_active_registrations,
    count_registrations_by_status,
    get_free_places,
)
from topics import LEVELS


def get_event_statistics(events: dict[int, dict],
                         registrations: list[dict]) -> dict[int, dict]:
    """Собрать сводку по каждому мероприятию.

    Для каждого мероприятия вычисляются вместимость, число занятых
    мест, число заявок в листе ожидания, число посещений и доля
    заполненности в процентах.
    """
    summary: dict[int, dict] = {}
    for event_id, event in events.items():
        capacity = int(event["capacity"])
        signed_up = count_active_registrations(registrations, event_id)
        summary[event_id] = {
            "capacity": capacity,
            "signed_up": signed_up,
            "free_places": get_free_places(signed_up, capacity),
            "waiting": count_registrations_by_status(
                registrations, event_id, STATUS_PENDING
            ),
            "attended": count_registrations_by_status(
                registrations, event_id, STATUS_ATTENDED
            ),
            "cancelled": count_registrations_by_status(
                registrations, event_id, STATUS_CANCELLED
            ),
            "fill_percent": percent(signed_up, capacity),
        }
    return summary


def get_club_event_counts(events: dict[int, dict]) -> dict[int, int]:
    """Посчитать число мероприятий каждого клуба.

    Клубы без мероприятий в словарь не попадают: их счётчик равен нулю
    и при обращении возвращается значением по умолчанию.
    """
    counts: dict[int, int] = {}
    for event in events.values():
        club_id = event["club_id"]
        counts[club_id] = counts.get(club_id, 0) + 1
    return counts


def count_topics_by_level(topics: dict[int, dict]) -> dict[str, int]:
    """Посчитать число тем дискуссий по уровню сложности.

    В результате присутствуют все уровни, включая уровни без тем: иначе
    в отчёте появляются пропуски в строках таблицы.
    """
    counts = {level: 0 for level in LEVELS}
    for topic in topics.values():
        counts[topic["level"]] = counts.get(topic["level"], 0) + 1
    return counts


def get_top_participants(registrations: list[dict],
                         limit: int = 5) -> list[tuple[str, int]]:
    """Получить самых активных участников.

    Возвращает пары «имя, число регистраций», отсортированные по
    убыванию активности. Отменённые заявки не учитываются.
    """
    counter: dict[str, int] = {}
    for record in registrations:
        if record["status"] == STATUS_CANCELLED:
            continue
        name = str(record["name"])
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


def format_event_statistics(title: str, events: dict[int, dict],
                            summary: dict[int, dict]) -> str:
    """Оформить сводку по мероприятиям в виде таблицы."""
    lines = [title, "-" * len(title)]
    header = (
        f"{'ID':>3} {'Дата':>10} {'Мест':>5} {'Занято':>7} "
        f"{'Свободно':>8} {'Заполнено':>10}"
    )
    lines.append(header)
    for event_id in sorted(summary):
        event = events.get(event_id)
        if event is None:
            continue
        row = summary[event_id]
        lines.append(
            f"{event_id:>3} "
            f"{event['event_date'].strftime('%d.%m.%Y'):>10} "
            f"{row['capacity']:>5} "
            f"{row['signed_up']:>7} "
            f"{row['free_places']:>8} "
            f"{str(row['fill_percent']) + '%':>10}"
        )
    return "\n".join(lines)


def format_topics_by_level(counts: dict[str, int]) -> str:
    """Оформить число тем по уровням сложности в виде таблицы."""
    lines = ["Темы по уровням сложности", "-" * 25]
    for level, count in counts.items():
        lines.append(f"{level:<14} — {count}")
    return "\n".join(lines)
