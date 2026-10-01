"""Работа с дискуссионными клубами.

Клубы представлены объектами класса models.club.Club, коллекция клубов
— это список объектов List[Club].

Модуль содержит только операции над коллекцией: поиск, фильтрацию и
сортировку. Данные и поведение самого клуба описаны методами класса
Club, поэтому функциям модуля достаточно обращаться к атрибутам
объекта: club.name, club.moderator.

Функции модуля не изменяют чужие коллекции и не читают файлы: работа
с ними выполняется в модулях storage.py и main.py.
"""

from typing import Iterator, List, Optional

from models import Club
from utils import next_id


def add_club(clubs: List[Club], name: str, description: str,
             moderator: str) -> Club:
    """Создать объект клуба и добавить его в коллекцию.

    Возвращает созданный объект Club: идентификатор нового клуба
    доступен как club.id, а сам клуб уже находится в списке.
    """
    club = Club(
        club_id=next_id(club.id for club in clubs),
        name=name,
        description=description,
        moderator=moderator,
    )
    clubs.append(club)
    return club


def get_club(clubs: List[Club], club_id: int) -> Optional[Club]:
    """Вернуть объект клуба по идентификатору.

    Если клуб не найден, возвращается None: вызывающий код сам решает,
    как сообщить пользователю об отсутствии клуба.
    """
    for club in clubs:
        if club.id == club_id:
            return club
    return None


def find_club(clubs: List[Club], query: str) -> List[Club]:
    """Найти клубы по подстроке названия или описания.

    Возвращает список объектов Club. Регистр и пробелы в запросе
    не учитываются: сравнение выполняет метод Club.matches().
    Пустой список означает, что подходящих клубов нет.
    """
    return [club for club in clubs if club.matches(query)]


def iter_club_names(clubs: List[Club]) -> Iterator[str]:
    """Генератор: последовательно выдавать названия клубов.

    Клубы перебираются по алфавиту. Генератор применяется там, где
    значения нужны по одному: при выводе и при подсчёте.
    """
    for club in sort_clubs_by_name(clubs):
        yield club.name


def sort_clubs_by_name(clubs: List[Club]) -> List[Club]:
    """Отсортировать клубы по названию.

    Ключ сортировки задан lambda-функцией: без неё сравнение шло бы
    по идентификатору.
    """
    return sorted(clubs, key=lambda club: normalize(club.name))


def sort_clubs_by_size(clubs: List[Club],
                       club_sizes: dict) -> List[Club]:
    """Отсортировать клубы по количеству мероприятий.

    Сортировка выполняется по убыванию: сначала самые активные клубы.
    Клубы без мероприятий получают нулевое значение.
    """
    return sorted(
        clubs,
        key=lambda club: club_sizes.get(club.id, 0),
        reverse=True,
    )


def get_club_card(club: Club) -> str:
    """Сформировать текстовую карточку клуба для вывода."""
    return club.render()


def normalize(value: object) -> str:
    """Привести значение к строке для сравнения без учёта регистра."""
    return str(value).strip().lower()
