"""Класс Registration — заявка участника на мероприятие.

Заявка хранит данные участника и своё состояние. Изменение состояния
выполняют методы confirm() и cancel(): снаружи нельзя присвоить
статус произвольной строки, поскольку свойство status проверяет
значение.

Заявка связана с мероприятием: объект registration.event позволяет
получить дату, клуб и требования мероприятия, не обращаясь к
коллекции. Идентификатор мероприятия остаётся в атрибуте event_id:
именно он сохраняется в JSON-файле.
"""

import datetime
from random import randint
from typing import Any, Dict, Optional

from .base import BaseEntity
from .event import Event

STATUS_PENDING = "ожидает подтверждения"
STATUS_CONFIRMED = "подтверждён"
STATUS_ATTENDED = "присутствовал"
STATUS_CANCELLED = "отменён"

REGISTRATION_STATUSES = (
    STATUS_PENDING,
    STATUS_CONFIRMED,
    STATUS_ATTENDED,
    STATUS_CANCELLED,
)

#: Место занимают только эти статусы: заявки листа ожидания и
#: отменённые заявки освобождают место на мероприятии.
PLACEHOLDING_STATUSES = (STATUS_CONFIRMED, STATUS_ATTENDED)

CANCELLED_STATUS = STATUS_CANCELLED
CONFIRMED_STATUS = STATUS_CONFIRMED


class Registration(BaseEntity):
    """Заявка участника на участие в мероприятии."""

    KIND = "регистрация"

    def __init__(self, registration_id: int, event_id: int, name: str,
                 age: int, level: str, has_read_materials: bool,
                 status: str = STATUS_PENDING,
                 ticket_code: str = "",
                 event: Optional[Event] = None) -> None:
        """Создать объект регистрации.

        Args:
            registration_id: Уникальный идентификатор заявки.
            event_id: Идентификатор мероприятия.
            name: Имя участника.
            age: Возраст участника.
            level: Уровень подготовки участника.
            has_read_materials: Прочитаны ли рекомендованные материалы.
            status: Статус заявки: по умолчанию лист ожидания.
            ticket_code: Код участия: создаётся автоматически.
            event: Объект мероприятия, если связь уже установлена.
        """
        super().__init__(registration_id)
        self.event_id = int(event_id)
        self.name = str(name)
        self.age = int(age)
        self.level = str(level)
        self.has_read_materials = bool(has_read_materials)
        self.status = status
        self.ticket_code = ticket_code or self.generate_ticket_code()
        self.event = event
        self.confirmed_at = ""

    @property
    def status(self) -> str:
        """Вернуть статус заявки."""
        return self._status

    @status.setter
    def status(self, value: str) -> None:
        """Задать статус заявки.

        Значение проверяется: неизвестный статус означает ошибку в
        данных, и её лучше увидеть сразу.
        """
        if value not in REGISTRATION_STATUSES:
            raise ValueError(f"Неизвестный статус заявки: {value}")
        self._status = value

    @staticmethod
    def generate_ticket_code() -> str:
        """Создать код участия, например DC-4821.

        Метод не использует данные экземпляра, поэтому объявлен
        статическим: вызывается как Registration.generate_ticket_code().
        """
        return f"DC-{randint(1000, 9999):04d}"

    @classmethod
    def from_data(cls, data: Dict[str, Any],
                  registration_id: Optional[int] = None,
                  event: Optional[Event] = None) -> "Registration":
        """Создать объект регистрации из данных JSON."""
        identifier = data.get("id", registration_id)
        if identifier is None:
            raise ValueError(
                "В данных регистрации отсутствует идентификатор"
            )
        return cls(
            registration_id=int(identifier),
            event_id=data.get("event_id", 0),
            name=data.get("name", ""),
            age=data.get("age", 0),
            level=data.get("level", ""),
            has_read_materials=data.get("has_read_materials", False),
            status=data.get("status", STATUS_PENDING),
            ticket_code=data.get("ticket_code", ""),
            event=event,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать регистрацию в данные для JSON-файла.

        В файл записывается идентификатор мероприятия, а не сам
        объект: JSON хранит только данные, а не структуру Python.
        """
        return {
            "id": self.id,
            "event_id": self.event_id,
            "name": self.name,
            "age": self.age,
            "level": self.level,
            "has_read_materials": self.has_read_materials,
            "status": self._status,
            "ticket_code": self.ticket_code,
        }

    def link(self, event: Optional[Event]) -> None:
        """Связать регистрацию с объектом мероприятия."""
        if event is not None:
            self.event = event

    @property
    def is_active(self) -> bool:
        """Вернуть признак того, что заявка ещё не отменена."""
        return self._status != STATUS_CANCELLED

    @property
    def occupies_place(self) -> bool:
        """Вернуть признак того, что заявка занимает место."""
        return self._status in PLACEHOLDING_STATUSES

    def is_waiting(self) -> bool:
        """Проверить, находится ли заявка в листе ожидания."""
        return self._status == STATUS_PENDING

    def is_cancelled(self) -> bool:
        """Проверить, отменена ли заявка."""
        return self._status == STATUS_CANCELLED

    def confirm(self, moment: Optional[datetime.date] = None) -> None:
        """Подтвердить заявку, заняв место на мероприятии.

        Подтверждается только заявка листа ожидания: подтверждённая и
        отменённая заявка повторно подтверждаются не будут.
        """
        if self._status != STATUS_PENDING:
            return
        self._status = STATUS_CONFIRMED
        if moment is None:
            moment = datetime.date.today()
        self.confirmed_at = moment.isoformat()

    def cancel(self) -> None:
        """Отменить заявку и освободить место на мероприятии.

        Объект остаётся в коллекции: сохраняется информация о том,
        что участник регистрировался ранее.
        """
        self._status = STATUS_CANCELLED
        self.confirmed_at = ""

    def event_date_text(self) -> str:
        """Вернуть дату мероприятия в виде ДД.ММ.ГГГГ."""
        if self.event is None:
            return "мероприятие не найдено"
        return self.event.event_date.strftime("%d.%m.%Y")

    def describe(self) -> str:
        """Вернуть строку «регистрация <id> — <имя>, <статус>»."""
        return (
            f"Регистрация {self.id} — {self.name}, {self._status}"
        )

    def render(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Сформировать карточку регистрации для вывода."""
        materials = "да" if self.has_read_materials else "нет"
        start_time = ""
        if self.event is not None:
            start_time = self.event.start_time
        return (
            f"Участник: {self.name}, возраст {self.age}, "
            f"уровень «{self.level}», материалы прочитаны: {materials}\n"
            f"Мероприятие: {self.event_date_text()}, {start_time}\n"
            f"Статус заявки: {self._status}\n"
            f"Код участия: {self.ticket_code}"
        )
