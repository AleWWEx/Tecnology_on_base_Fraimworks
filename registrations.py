"""Работа с регистрациями участников на мероприятия.

Регистрации представлены объектами класса models.registration.
Registration, коллекция регистраций — это список объектов
List[Registration].

Модуль содержит логику начального сценария ПР1 (check_requirements,
get_registration_result, generate_ticket_code), переработанную для
работы с коллекциями: требования мероприятия берутся из объекта
Event, а не из констант модуля.

Распределение ответственности:

- изменение состояния заявки выполняют методы объекта confirm()
  и cancel();
- функции модуля ищут заявки в коллекции и создают новые объекты.
"""

import datetime
from typing import List, Optional, Tuple

from events import (
    STATUS_FINISHED,
    STATUS_PENDING,
    count_active_registrations,
    get_event,
)
from models import Event, Registration, check_event_requirements
from utils import next_id

RESULT_APPROVED = "подтверждена"
RESULT_WAITING = "лист ожидания"
RESULT_REJECTED = "отказано"

MIN_PRIORITY_AGE = 18
PRIORITY_FREE_PLACES = 3

__all__ = [
    "RESULT_APPROVED",
    "RESULT_REJECTED",
    "RESULT_WAITING",
    "cancel_registration",
    "check_requirements",
    "confirm_registration",
    "create_registration",
    "filter_registrations_by_status",
    "find_registrations_by_name",
    "generate_ticket_code",
    "get_availability_text",
    "get_registration_card",
    "get_registration_result",
    "is_event_available",
    "next_registration_id",
]


def check_requirements(age: int, level: str, has_read_materials: bool,
                       min_age: int, required_level: str) -> str:
    """Проверить требования мероприятия.

    Возвращает текст первой невыполненной причины. Если все требования
    выполнены, возвращается пустая строка. Функция ПР1 сохранена: у
    объекта мероприятия есть одноимённый метод Event.check_requirements,
    который использует данные конкретного мероприятия.
    """
    return check_event_requirements(
        age, level, has_read_materials, min_age, required_level
    )


def get_registration_result(age: int, level: str, has_read_materials: bool,
                            event_status: str, free_places: int,
                            min_age: int,
                            required_level: str) -> Tuple[str, str]:
    """Принять решение по заявке участника.

    Возвращает пару: результат обработки заявки и его пояснение.
    Функция сценария ПР1 сохранена без изменений по назначению.
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
    """Создать код участия, например DC-4821.

    Функция ПР1 сохранена. Тот же код создаёт статический метод
    Registration.generate_ticket_code(), который вызывается
    конструктором заявки.
    """
    return Registration.generate_ticket_code()


def get_availability_text(is_available: bool) -> str:
    """Вернуть текстовый статус доступности мероприятия.

    Функция вызывается по результату проверки is_event_available:
    короткая функция текста вынесена отдельно от самой проверки.
    """
    if is_available:
        return "Мероприятие доступно для записи"
    return "Мероприятие недоступно для записи"


def is_event_available(events: List[Event],
                       registrations: List[Registration],
                       event_id: int,
                       today: Optional[datetime.date] = None) -> bool:
    """Проверить, доступно ли мероприятие для новой регистрации.

    Мероприятие доступно, если оно ещё не завершено и на нём остались
    свободные места. Проверку выполняет метод Event.is_available():
    функция модуля лишь находит объект мероприятия и передаёт ему
    число занятых мест.
    """
    event = get_event(events, event_id)
    if event is None:
        return False
    signed_up = count_active_registrations(registrations, event_id)
    return event.is_available(signed_up, today)


def create_registration(registrations: List[Registration], event_id: int,
                        name: str, age: int, level: str,
                        has_read_materials: bool,
                        status: str = STATUS_PENDING) -> Registration:
    """Создать объект регистрации и добавить его в коллекцию.

    Новая заявка получает код участия и указанный статус: подтверждённую
    заявку сразу подтверждают, ожидающую помещают в лист ожидания.
    Возвращает созданный объект Registration.
    """
    registration = Registration(
        registration_id=next_registration_id(registrations),
        event_id=event_id,
        name=name,
        age=age,
        level=level,
        has_read_materials=has_read_materials,
        status=status,
    )
    registrations.append(registration)
    return registration


def next_registration_id(registrations: List[Registration]) -> int:
    """Вычислить идентификатор для новой регистрации."""
    return next_id(item.id for item in registrations)


def cancel_registration(registrations: List[Registration],
                        registration_id: int) -> bool:
    """Отменить регистрацию по её идентификатору.

    Состояние объекта меняет метод Registration.cancel(), сама
    функция только находит заявку в коллекции. Возвращает True,
    если запись найдена и отменена. Повторная отмена уже отменённой
    регистрации ничего не меняет и тоже возвращает True.
    """
    registration = get_registration(registrations, registration_id)
    if registration is None:
        return False
    registration.cancel()
    return True


def confirm_registration(registrations: List[Registration],
                         registration_id: int) -> bool:
    """Подтвердить заявку, ожидающую подтверждения.

    Состояние объекта меняет метод Registration.confirm(). Заявка со
    статусом «присутствовал» и отменённая заявка не подтверждаются:
    возвращается False.
    """
    registration = get_registration(registrations, registration_id)
    if registration is None or not registration.is_waiting():
        return False
    registration.confirm()
    return True


def get_registration(registrations: List[Registration],
                     registration_id: int) -> Optional[Registration]:
    """Вернуть объект регистрации по идентификатору или None."""
    for registration in registrations:
        if registration.id == registration_id:
            return registration
    return None


def find_registrations_by_name(registrations: List[Registration],
                               name: str) -> List[Registration]:
    """Найти регистрации участника по подстроке имени.

    Сравнение выполняется без учёта регистра.
    """
    needle = str(name).strip().lower()
    return [
        registration
        for registration in registrations
        if needle in registration.name.lower()
    ]


def filter_registrations_by_status(registrations: List[Registration],
                                   status: str) -> List[Registration]:
    """Отобрать регистрации с заданным статусом."""
    return [
        registration
        for registration in registrations
        if registration.status == status
    ]


def get_registration_card(registration: Registration) -> str:
    """Сформировать текстовую карточку регистрации для вывода."""
    return registration.render()


def link_registrations(registrations: List[Registration],
                       events: List[Event]) -> None:
    """Связать каждую регистрацию с объектом её мероприятия.

    Связь выполняется при загрузке данных: объект регистрации получает
    ссылку на объект мероприятия, а в JSON-файле по-прежнему хранится
    только идентификатор event_id.
    """
    for registration in registrations:
        event = get_event(events, registration.event_id)
        registration.link(event)
