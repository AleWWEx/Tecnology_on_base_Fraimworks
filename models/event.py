"""Класс Event — мероприятие дискуссионного клуба.

Мероприятие — центральная сущность проекта: оно ссылается на клуб и
тему, хранит дату, время, формат, место, вместимость и требования к
участнику. Вместимость скрыта за свойством: отрицательное значение
нельзя передать в объект.

В модуле собраны функции предметной области, которые в ПР2 были
обычными функциями над словарями: определение статуса по дате,
подсчёт свободных мест и проверка требований к участнику.
"""

import datetime
from typing import Any, Dict, Optional

from .base import BaseEntity

STATUS_PLANNED = "планируется"
STATUS_RUNNING = "идёт"
STATUS_FINISHED = "завершено"

EVENT_FORMATS = ("онлайн", "офлайн")

REQUIREMENT_OK = ""


def calculate_event_status(event_date: datetime.date,
                           today: Optional[datetime.date] = None) -> str:
    """Определить статус мероприятия по дате его проведения.

    Если опорная дата не передана, используется текущая дата.
    """
    if today is None:
        today = datetime.date.today()
    if event_date < today:
        return STATUS_FINISHED
    if event_date == today:
        return STATUS_RUNNING
    return STATUS_PLANNED


def count_free_places(participants: int, capacity: int) -> int:
    """Вернуть число свободных мест, не меньшее нуля."""
    free_places = capacity - participants
    if free_places < 0:
        return 0
    return free_places


def check_event_requirements(age: int, level: str,
                             has_read_materials: bool, min_age: int,
                             required_level: str) -> str:
    """Проверить требования мероприятия к участнику.

    Возвращает текст первой невыполненной причины. Если все требования
    выполнены, возвращается пустая строка.
    """
    if age < min_age:
        return f"возраст {age} лет меньше допустимых {min_age}"
    if not has_read_materials:
        return "рекомендованные материалы не прочитаны"
    if level != required_level:
        return f"уровень «{level}» не подходит, нужен «{required_level}»"
    return REQUIREMENT_OK


class Event(BaseEntity):
    """Мероприятие клуба, на которое принимаются заявки."""

    KIND = "мероприятие"

    def __init__(self, event_id: int, club_id: int, topic_id: int,
                 event_date: datetime.date, start_time: str,
                 event_format: str, place: str, capacity: int,
                 min_age: int, required_level: str) -> None:
        """Создать объект мероприятия.

        Args:
            event_id: Уникальный идентификатор мероприятия.
            club_id: Идентификатор клуба, который проводит встречу.
            topic_id: Идентификатор обсуждаемой темы.
            event_date: Дата проведения.
            start_time: Время начала в формате ЧЧ:ММ.
            event_format: Формат встречи: онлайн или офлайн.
            place: Место проведения или описание ссылки.
            capacity: Вместимость мероприятия.
            min_age: Минимальный возраст участника.
            required_level: Требуемый уровень подготовки.
        """
        super().__init__(event_id)
        self.club_id = int(club_id)
        self.topic_id = int(topic_id)
        self.event_date = event_date
        self.start_time = str(start_time)
        self.format = str(event_format)
        self.place = str(place)
        self.capacity = capacity
        self.min_age = int(min_age)
        self.required_level = str(required_level)
        self.club = None
        self.topic = None

    @property
    def capacity(self) -> int:
        """Вернуть вместимость мероприятия."""
        return self._capacity

    @capacity.setter
    def capacity(self, value: int) -> None:
        """Задать вместимость мероприятия.

        Вместимость меньше нуля не допускается: такое значение
        привело бы к отрицательному числу свободных мест.
        """
        number = int(value)
        if number < 0:
            raise ValueError("Вместимость не может быть отрицательной")
        self._capacity = number

    @classmethod
    def from_data(cls, data: Dict[str, Any],
                  event_id: Optional[int] = None,
                  parse_date: Optional[Any] = None) -> "Event":
        """Создать объект мероприятия из данных JSON.

        Параметр parse_date — функция разбора даты формата ГГГГ-ММ-ДД.
        Если она не передана, дата должна быть объектом date.
        """
        identifier = data.get("id", event_id)
        if identifier is None:
            raise ValueError("В данных мероприятия отсутствует идентификатор")
        raw_date = data.get("event_date")
        if parse_date is not None:
            event_date = parse_date(str(raw_date))
        else:
            event_date = raw_date
        return cls(
            event_id=int(identifier),
            club_id=data.get("club_id", 0),
            topic_id=data.get("topic_id", 0),
            event_date=event_date,
            start_time=data.get("start_time", ""),
            event_format=data.get("format", ""),
            place=data.get("place", ""),
            capacity=data.get("capacity", 0),
            min_age=data.get("min_age", 0),
            required_level=data.get("required_level", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать мероприятие в данные для events.json."""
        return {
            "id": self.id,
            "club_id": self.club_id,
            "topic_id": self.topic_id,
            "event_date": self.event_date.isoformat(),
            "start_time": self.start_time,
            "format": self.format,
            "place": self.place,
            "capacity": self.capacity,
            "min_age": self.min_age,
            "required_level": self.required_level,
        }

    def link(self, club: Any = None, topic: Any = None) -> None:
        """Связать мероприятие с объектами клуба и темы.

        В коллекциях хранятся идентификаторы, а объект хранит ссылки
        на связанные объекты: так данные доступны без поиска.
        """
        if club is not None:
            self.club = club
        if topic is not None:
            self.topic = topic

    def status_on(self, today: Optional[datetime.date] = None) -> str:
        """Вернуть статус мероприятия на указанную дату."""
        return calculate_event_status(self.event_date, today)

    @property
    def status(self) -> str:
        """Вернуть статус мероприятия на текущую дату."""
        return self.status_on()

    def free_places(self, participants: int) -> int:
        """Вернуть число свободных мест для указанного числа участников."""
        return count_free_places(participants, self.capacity)

    def is_available(self, participants: int,
                     today: Optional[datetime.date] = None) -> bool:
        """Проверить, принимает ли мероприятие новые заявки.

        Мероприятие доступно, если оно ещё не завершено и на нём
        остались свободные места.
        """
        if self.status_on(today) == STATUS_FINISHED:
            return False
        return self.free_places(participants) > 0

    def is_full(self, participants: int) -> bool:
        """Проверить, заняты ли все места мероприятия."""
        return participants >= self.capacity

    def check_requirements(self, age: int, level: str,
                           has_read_materials: bool) -> str:
        """Проверить требования мероприятия к участнику.

        Метод использует данные конкретного мероприятия: возраст и
        требуемый уровень. Пустая строка означает, что требования
        выполнены.
        """
        return check_event_requirements(
            age, level, has_read_materials, self.min_age,
            self.required_level,
        )

    def club_name(self) -> str:
        """Вернуть название клуба, проводящего мероприятие."""
        if self.club is None:
            return "клуб не найден"
        return self.club.name

    def topic_title(self) -> str:
        """Вернуть название обсуждаемой темы."""
        if self.topic is None:
            return "тема не найдена"
        return self.topic.title

    def describe(self) -> str:
        """Вернуть строку «мероприятие <id> — <дата>, <тема>»."""
        date_text = self.event_date.strftime("%d.%m.%Y")
        return f"Мероприятие {self.id} — {date_text}, {self.topic_title()}"

    def render(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Сформировать карточку мероприятия для вывода.

        В context передаются данные о числе занятых мест и статусе:
        они вычисляются по коллекции регистраций в модуле events.py.
        """
        participants = 0
        status = self.status
        if context:
            participants = int(context.get("participants", 0))
            status = str(context.get("status", status))
        free = self.free_places(participants)
        topic_level = "—"
        if self.topic is not None:
            topic_level = self.topic.level
        return (
            f"Клуб: {self.club_name()}\n"
            f"Тема: {self.topic_title()}\n"
            f"Уровень темы: {topic_level}\n"
            f"Дата: {self.event_date.strftime('%d.%m.%Y')}, начало в "
            f"{self.start_time}\n"
            f"Формат: {self.format} ({self.place})\n"
            f"Требования: возраст {self.min_age}+, уровень "
            f"«{self.required_level}», рекомендованные материалы "
            "прочитаны\n"
            f"Места: занято {participants} из {self.capacity}, "
            f"свободно {free}\n"
            f"Статус мероприятия: {status}"
        )
