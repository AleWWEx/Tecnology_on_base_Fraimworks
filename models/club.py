"""Класс Club — дискуссионный клуб.

Клуб хранит название, описание и модератора. Создание объектов,
строковое представление и преобразование в данные JSON реализованы
методами класса, а поиск и сортировка клубов остались функциями
модуля clubs.py: они работают с коллекцией, а не с отдельным клубом.
"""

from typing import Any, Dict, Optional

from .base import BaseEntity


class Club(BaseEntity):
    """Дискуссионный клуб."""

    KIND = "клуб"

    def __init__(self, club_id: int, name: str, description: str,
                 moderator: str) -> None:
        """Создать объект клуба.

        Args:
            club_id: Уникальный идентификатор клуба.
            name: Название клуба.
            description: Краткое описание клуба.
            moderator: Модератор клуба.
        """
        super().__init__(club_id)
        self.name = str(name)
        self.description = str(description)
        self.moderator = str(moderator)

    @classmethod
    def from_data(cls, data: Dict[str, Any],
                  club_id: Optional[int] = None) -> "Club":
        """Создать объект клуба из данных JSON.

        Идентификатор может приходить как отдельный аргумент: в
        коллекциях ПР2 он был ключом словаря.
        """
        identifier = data.get("id", club_id)
        if identifier is None:
            raise ValueError("В данных клуба отсутствует идентификатор")
        return cls(
            club_id=int(identifier),
            name=data.get("name", ""),
            description=data.get("description", ""),
            moderator=data.get("moderator", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать клуб в словарь для файла data/clubs.json."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "moderator": self.moderator,
        }

    def matches(self, query: str) -> bool:
        """Проверить, содержит ли клуб подстроку запроса.

        Сравнение выполняется без учёта регистра и лишних пробелов.
        """
        needle = str(query).strip().lower()
        haystack = f"{self.name} {self.description}".lower()
        return needle in haystack

    def describe(self) -> str:
        """Вернуть строку «клуб <id> — <название>»."""
        return f"Клуб {self.id} — «{self.name}»"

    def render(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Сформировать карточку клуба для вывода."""
        event_count = 0
        if context:
            event_count = int(context.get("event_count", 0))
        return (
            f"Клуб: {self.name}\n"
            f"Модератор: {self.moderator}\n"
            f"Описание: {self.description}\n"
            f"Мероприятий: {event_count}"
        )
