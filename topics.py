"""Работа с темами дискуссий.

Темы хранятся в словаре topics: ключ — идентификатор темы, значение —
словарь с данными темы (название, уровень сложности, теги, материалы).
Уровень сложности определяет, кому подходит тема, поэтому хранится
отдельно и используется при проверке заявки участника.
"""

from typing import Iterator

from utils import next_id

LEVELS = ("начинающий", "средний", "продвинутый")
LEVEL_ORDER = {level: number for number, level in enumerate(LEVELS)}


def add_topic(topics: dict[int, dict], title: str, level: str,
              tags: list[str], materials: str) -> int:
    """Добавить тему дискуссии в словарь topics.

    Идентификатор записывается и в ключ словаря, и в данные темы: без
    него запись нельзя сохранить в JSON-файл и прочитать обратно.
    Теги сохраняются без повторов и в порядке ввода: сравнение тегов не
    зависит от регистра. Возвращает идентификатор созданной темы.
    """
    topic_id = next_id(topics)
    unique_tags = []
    seen = set()
    for tag in tags:
        tag_stripped = tag.strip()
        key = tag_stripped.lower()
        if key and key not in seen:
            unique_tags.append(tag_stripped)
            seen.add(key)
    topics[topic_id] = {
        "id": topic_id,
        "title": title,
        "level": level,
        "tags": unique_tags,
        "materials": materials,
    }
    return topic_id


def get_topic(topics: dict[int, dict], topic_id: int) -> dict | None:
    """Вернуть данные темы по идентификатору или None."""
    return topics.get(topic_id)


def find_topics_by_tag(topics: dict[int, dict], tag: str) -> list[int]:
    """Найти темы, у которых указан заданный тег.

    Сравнение выполняется без учёта регистра. Пустой список означает,
    что темы с таким тегом нет.
    """
    needle = tag.strip().lower()
    return [
        topic_id
        for topic_id, topic in topics.items()
        if needle in {value.lower() for value in topic["tags"]}
    ]


def filter_topics_by_level(topics: dict[int, dict],
                           level: str) -> Iterator[int]:
    """Генератор: выдавать идентификаторы тем заданного уровня.

    Генератор не создаёт список целиком, поэтому используется там, где
    подходящие темы нужны для последовательного вывода.
    """
    for topic_id, topic in sorted(topics.items()):
        if topic["level"] == level:
            yield topic_id


def sort_topics_by_level(topics: dict[int, dict]) -> list[int]:
    """Отсортировать темы по сложности: от простых к сложным.

    Ключ сортировки задан lambda-функцией, обращающейся к словарю
    LEVEL_ORDER: сортировка строк дала бы другой порядок.
    """
    return sorted(
        topics,
        key=lambda topic_id: LEVEL_ORDER[topics[topic_id]["level"]],
    )


def get_topic_card(topic: dict) -> str:
    """Сформировать текстовую карточку темы для вывода."""
    tags = ", ".join(topic["tags"])
    return (
        f"Тема: {topic['title']}\n"
        f"Уровень: {topic['level']}\n"
        f"Теги: {tags}\n"
        f"Материалы: {topic['materials']}"
    )
