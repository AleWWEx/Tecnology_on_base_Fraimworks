"""Пакет моделей предметной области проекта.

Модули пакета содержат классы и не импортируют модули верхнего уровня:
такое направление зависимостей исключает циклические импорты. Классы
импортируются из пакета:

    from models import Club, Topic, Event, Registration
"""

from .base import BaseEntity
from .club import Club
from .event import (
    EVENT_FORMATS,
    STATUS_FINISHED,
    STATUS_PLANNED,
    STATUS_RUNNING,
    Event,
    calculate_event_status,
    check_event_requirements,
    count_free_places,
)
from .registration import (
    PLACEHOLDING_STATUSES,
    REGISTRATION_STATUSES,
    STATUS_ATTENDED,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    Registration,
)
from .topic import Topic

__all__ = [
    "BaseEntity",
    "Club",
    "Event",
    "Registration",
    "Topic",
    "EVENT_FORMATS",
    "PLACEHOLDING_STATUSES",
    "REGISTRATION_STATUSES",
    "STATUS_ATTENDED",
    "STATUS_CANCELLED",
    "STATUS_CONFIRMED",
    "STATUS_FINISHED",
    "STATUS_PENDING",
    "STATUS_PLANNED",
    "STATUS_RUNNING",
    "calculate_event_status",
    "check_event_requirements",
    "count_free_places",
]
