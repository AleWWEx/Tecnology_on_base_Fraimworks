"""Работа с регистрациями участников на мероприятия.

Регистрации хранятся в списке registrations: каждая запись — словарь с
идентификатором, мероприятием, данными участника и статусом заявки.

Модуль содержит логику начального сценария ПР1 (check_requirements,
get_registration_result, generate_ticket_code), переработанную для
работы с коллекциями: требования мероприятия берутся из данных
мероприятия, а не из констант модуля.
"""

import datetime
from random import randint
from typing import Optional

from events import (
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_FINISHED,
    STATUS_PENDING,
    count_active_registrations,
    get_event,
    get_event_status,
    get_free_places,
)

RESULT_APPROVED = "подтверждена"
RESULT_WAITING = "лист ожидания"
RESULT_REJECTED = "отказано"

MIN_PRIORITY_AGE = 18
PRIORITY_FREE_PLACES = 3


def check_requirements(age: int, level: str, has_read_materials: bool,
                       min_age: int, required_level: str) -> str:
    """Проверить требования мероприятия.

    Возвращает текст первой невыполненной причины. Если все требования
    выполнены, возвращается пустая строка.
    """
    if age < min_age:
        return f"возраст {age} лет меньше допустимых {min_age}"
    if not has_read_materials:
        return "рекомендованные материалы не прочитаны"
    if level != required_level:
        return f"уровень «{level}» не подходит, нужен «{required_level}»"
    return ""


def get_registration_result(age: int, level: str, has_read_materials: bool,
                            event_status: str, free_places: int,
                            min_age: int,
                            required_level: str) -> tuple[str, str]:
    """Принять решение по заявке участника.

    Возвращает пару: результат обработки заявки и его пояснение.
    """
    if event_status == STATUS_FINISHED:
        return RESULT_REJECTED, "мероприятие уже завершено"

    reason = check_requirements(
        age, level, has_read_materials, min_age, required_level
    )
    if reason != "":
        return RESULT_REJECTED, reason

    if free_places == 0:
        return RESULT_WAITING, "свободных мест нет"

    if free_places < PRIORITY_FREE_PLACES and age < MIN_PRIORITY_AGE:
        return RESULT_WAITING, (
            f"приоритет у участников {MIN_PRIORITY_AGE} лет и старше"
        )

    return RESULT_APPROVED, "требования выполнены, места есть"


def generate_ticket_code() -> str:
    """Создать код участия, например DC-4821."""
    return f"DC-{randint(1000, 9999):04d}"


def get_availability_text(is_available: bool) -> str:
    """Вернуть текстовый статус доступности мероприятия.

    Функция вызывается по результату проверки is_event_available:
    короткая функция текста вынесена отдельно от самой проверки.
    """
    if is_available:
        return "Мероприятие доступно для записи"
    return "Мероприятие недоступно для записи"


def is_event_available(events: dict[int, dict], registrations: list[dict],
                       event_id: int,
                       today: Optional[datetime.date] = None) -> bool:
    """Проверить, доступно ли мероприятие для новой регистрации.

    Мероприятие доступно, если оно ещё не завершено и на нём остались
    свободные места.
    """
    event = get_event(events, event_id)
    if event is None:
        return False
    status = get_event_status(event["event_date"], today)
    if status == STATUS_FINISHED:
        return False
    signed_up = count_active_registrations(registrations, event_id)
    return get_free_places(signed_up, int(event["capacity"])) > 0


def create_registration(registrations: list[dict], event_id: int,
                        name: str, age: int, level: str,
                        has_read_materials: bool,
                        status: str = STATUS_PENDING) -> dict:
    """Добавить запись о регистрации в список registrations.

    Новая заявка получает код участия и указанный статус: подтверждённую
    заявку сразу подтверждают, ожидающую помещают в лист ожидания.
    Возвращает созданную запись.
    """
    record = {
        "id": next_registration_id(registrations),
        "event_id": event_id,
        "name": name,
        "age": age,
        "level": level,
        "has_read_materials": has_read_materials,
        "status": status,
        "ticket_code": generate_ticket_code(),
    }
    registrations.append(record)
    return record


def next_registration_id(registrations: list[dict]) -> int:
    """Вычислить идентификатор для новой регистрации."""
    identifiers = [int(record["id"]) for record in registrations]
    return max(identifiers, default=0) + 1


def cancel_registration(registrations: list[dict],
                        registration_id: int) -> bool:
    """Отменить регистрацию по её идентификатору.

    Возвращает True, если запись найдена и отменена. Повторная отмена
    уже отменённой регистрации ничего не меняет и тоже возвращает True.
    """
    for record in registrations:
        if record["id"] == registration_id:
            record["status"] = STATUS_CANCELLED
            return True
    return False


def confirm_registration(registrations: list[dict],
                         registration_id: int) -> bool:
    """Подтвердить заявку, ожидающую подтверждения.

    Заявка со статусом «присутствовал» и отменённая заявка не
    подтверждаются: возвращается False.
    """
    for record in registrations:
        if record["id"] != registration_id:
            continue
        if record["status"] != STATUS_PENDING:
            return False
        record["status"] = STATUS_CONFIRMED
        return True
    return False


def find_registrations_by_name(registrations: list[dict],
                               name: str) -> list[int]:
    """Найти регистрации участника по подстроке имени.

    Сравнение выполняется без учёта регистра.
    """
    needle = name.strip().lower()
    return [
        record["id"]
        for record in registrations
        if needle in str(record["name"]).lower()
    ]


def filter_registrations_by_status(registrations: list[dict],
                                   status: str) -> list[dict]:
    """Отобрать регистрации с заданным статусом."""
    return [record for record in registrations if record["status"] == status]


def get_registration_card(record: dict, event: dict) -> str:
    """Сформировать текстовую карточку регистрации для вывода."""
    materials = "да" if record["has_read_materials"] else "нет"
    return (
        f"Участник: {record['name']}, возраст {record['age']}, "
        f"уровень «{record['level']}», материалы прочитаны: {materials}\n"
        f"Мероприятие: {event['event_date'].strftime('%d.%m.%Y')}, "
        f"{event['start_time']}\n"
        f"Статус заявки: {record['status']}\n"
        f"Код участия: {record['ticket_code']}"
    )
