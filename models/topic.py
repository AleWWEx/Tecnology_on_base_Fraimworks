"""Класс Topic — тема дискуссии.

Тема хранит название, уровень сложности, теги и рекомендованные
материалы. Список тегов скрыт за свойством: внешний код получает
копию и не может изменить данные темы, не заметив этого.
"""

from typing import Any, Dict, Iterable, Optional, Tuple

from .base import BaseEntity


class Topic(BaseEntity):
    """Тема дискуссии."""

    KIND = "тема"

    def __init__(self, topic_id: int, title: str, level: str,
                 tags: Iterable[str], materials: str) -> None:
        """Создать объект темы.

        Args:
            topic_id: Уникальный идентификатор темы.
            title: Название темы.
            level: Уровень сложности темы.
            tags: Теги темы: повторы и лишние пробелы удаляются.
            materials: Рекомендованные материалы для подготовки.
        """
        super().__init__(topic_id)
        self.title = str(title)
        self.level = str(level)
        self._tags = self._clean_tags(tags)
        self.materials = str(materials)

    @staticmethod
    def _clean_tags(tags: Iterable[str]) -> list:
        """Очистить теги: обрезать пробелы и убрать повторы.

        Сравнение тегов не зависит от регистра, поэтому теги «ИИ» и
        «ии» считаются одним и тем же. Порядок ввода сохраняется.
        """
        cleaned = []
        seen = set()
        for tag in tags:
            value = str(tag).strip()
            key = value.lower()
            if key and key not in seen:
                cleaned.append(value)
                seen.add(key)
        return cleaned

    @property
    def tags(self) -> Tuple[str, ...]:
        """Вернуть теги темы.

        Возвращается кортеж: изменить данные темы по ссылки нельзя,
        для этого нужно создать новый объект.
        """
        return tuple(self._tags)

    @classmethod
    def from_data(cls, data: Dict[str, Any],
                  topic_id: Optional[int] = None) -> "Topic":
        """Создать объект темы из данных JSON."""
        identifier = data.get("id", topic_id)
        if identifier is None:
            raise ValueError("В данных темы отсутствует идентификатор")
        return cls(
            topic_id=int(identifier),
            title=data.get("title", ""),
            level=data.get("level", ""),
            tags=data.get("tags", []) or [],
            materials=data.get("materials", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать тему в словарь для файла data/topics.json."""
        return {
            "id": self.id,
            "title": self.title,
            "level": self.level,
            "tags": list(self._tags),
            "materials": self.materials,
        }

    def has_tag(self, tag: str) -> bool:
        """Проверить, есть ли у темы заданный тег.

        Регистр и лишние пробелы не учитываются.
        """
        needle = str(tag).strip().lower()
        return needle in {value.lower() for value in self._tags}

    def has_level(self, level: str) -> bool:
        """Проверить, совпадает ли уровень темы с заданным."""
        return self.level == str(level).strip().lower()

    def describe(self) -> str:
        """Вернуть строку «тема <id> — <название>»."""
        return f"Тема {self.id} — «{self.title}»"

    def render(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Сформировать карточку темы для вывода."""
        tags = ", ".join(self._tags)
        return (
            f"Тема: {self.title}\n"
            f"Уровень: {self.level}\n"
            f"Теги: {tags}\n"
            f"Материалы: {self.materials}"
        )
