"""Работа с дискуссионными клубами.

Клубы хранятся в словаре clubs: ключ словаря — идентификатор клуба,
значение — словарь с данными клуба (название, описание, модератор).
Функции модуля не изменяют чужие коллекции и не читают файлы: работа
с ними выполняется в модулях storage.py и main.py.
"""

from typing import Iterator

from utils import next_id


def add_club(clubs: dict[int, dict], name: str, description: str,
             moderator: str) -> int:
    """Добавить клуб в словарь clubs.

    Идентификатор записывается и в ключ словаря, и в данные клуба: без
    него запись нельзя сохранить в JSON-файл и прочитать обратно.
    Возвращает идентификатор созданного клуба.
    """
    club_id = next_id(clubs)
    clubs[club_id] = {
        "id": club_id,
        "name": name,
        "description": description,
        "moderator": moderator,
    }
    return club_id


def get_club(clubs: dict[int, dict], club_id: int) -> dict | None:
    """Вернуть данные клуба по идентификатору.

    Если клуб не найден, возвращается None: вызывающий код сам решает,
    как сообщить пользователю об отсутствии клуба.
    """
    return clubs.get(club_id)


def find_club(clubs: dict[int, dict], query: str) -> list[int]:
    """Найти клубы по подстроке названия или описания.

    Возвращает список идентификаторов найденных клубов. Регистр и
    пробелы в запросе не учитываются. Пустой список означает, что
    подходящих клубов нет.
    """
    needle = normalize(query)
    return [
        club_id
        for club_id, club in clubs.items()
        if needle in normalize(club["name"])
        or needle in normalize(club["description"])
    ]


def iter_club_names(clubs: dict[int, dict]) -> Iterator[str]:
    """Генератор: последовательно выдавать названия клубов.

    Клубы перебираются в порядке идентификаторов. Генератор применяется
    там, где значения нужны по одному: при выводе и при подсчёте.
    """
    for club_id in sort_club_ids_by_name(clubs):
        yield str(clubs[club_id]["name"])


def sort_club_ids_by_name(clubs: dict[int, dict]) -> list[int]:
    """Отсортировать клубы по названию.

    Возвращает список идентификаторов. Ключ сортировки задан
    lambda-функцией: без неё сравнение шло бы по идентификатору.
    """
    return sorted(
        clubs,
        key=lambda club_id: normalize(clubs[club_id]["name"]),
    )


def sort_club_ids_by_size(clubs: dict[int, dict],
                          club_sizes: dict[int, int]) -> list[int]:
    """Отсортировать клубы по количеству мероприятий.

    Сортировка выполняется по убыванию: сначала самые активные клубы.
    """
    return sorted(
        clubs,
        key=lambda club_id: club_sizes.get(club_id, 0),
        reverse=True,
    )


def get_club_card(club: dict) -> str:
    """Сформировать текстовую карточку клуба для вывода."""
    return (
        f"Клуб: {club['name']}\n"
        f"Модератор: {club['moderator']}\n"
        f"Описание: {club['description']}"
    )


def normalize(value: object) -> str:
    """Привести значение к строке для сравнения без учёта регистра."""
    return str(value).strip().lower()
