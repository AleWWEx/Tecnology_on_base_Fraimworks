"""Работа с темами дискуссий.

Темы представлены объектами класса models.topic.Topic, коллекция тем —
это список объектов List[Topic].

Проверка принадлежности тега и уровня перенесена в методы класса
Topic (has_tag, has_level): операция относится к самой теме. Функции
модуля работают с коллекцией тем: создают объекты, ищут их по признаку
и сортируют.

Уровень сложности определяет, кому подходит тема, поэтому хранится
отдельно и используется при проверке заявки участника.
"""

from typing import Iterator, List, Optional

from models import Topic
from utils import next_id

LEVELS = ("начинающий", "средний", "продвинутый")
LEVEL_ORDER = {level: number for number, level in enumerate(LEVELS)}


def add_topic(topics: List[Topic], title: str, level: str,
              tags: List[str], materials: str) -> Topic:
    """Создать объект темы и добавить его в коллекцию.

    Теги очищаются конструктором Topic: повторы и лишние пробелы
    удаляются, порядок ввода сохраняется. Возвращает созданный объект.
    """
    topic = Topic(
        topic_id=next_id(topic.id for topic in topics),
        title=title,
        level=level,
        tags=tags,
        materials=materials,
    )
    topics.append(topic)
    return topic


def get_topic(topics: List[Topic], topic_id: int) -> Optional[Topic]:
    """Вернуть объект темы по идентификатору или None."""
    for topic in topics:
        if topic.id == topic_id:
            return topic
    return None


def find_topics_by_tag(topics: List[Topic], tag: str) -> List[Topic]:
    """Найти темы, у которых указан заданный тег.

    Сравнение выполняется без учёта регистра: за это отвечает метод
    Topic.has_tag(). Пустой список означает, что темы с таким тегом
    нет.
    """
    return [topic for topic in topics if topic.has_tag(tag)]


def filter_topics_by_level(topics: List[Topic],
                           level: str) -> Iterator[Topic]:
    """Генератор: выдавать темы заданного уровня.

    Генератор не создаёт список целиком, поэтому используется там,
    где подходящие темы нужны для последовательного вывода.
    """
    for topic in sort_topics_by_level(topics):
        if topic.has_level(level):
            yield topic


def sort_topics_by_level(topics: List[Topic]) -> List[Topic]:
    """Отсортировать темы по сложности: от простых к сложным.

    Ключ сортировки задан lambda-функцией, обращающейся к словарю
    LEVEL_ORDER: сортировка строк дала бы другой порядок.
    """
    return sorted(topics, key=lambda topic: LEVEL_ORDER[topic.level])


def get_topic_card(topic: Topic) -> str:
    """Сформировать текстовую карточку темы для вывода."""
    return topic.render()
