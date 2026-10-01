"""Сохранение и загрузка данных проекта в JSON-файлах.

Формат хранения данных не изменился по сравнению с ПР2: файлы
data/clubs.json, data/topics.json, data/events.json и
data/registrations.json содержат те же поля. Изменился способ работы:

- при загрузке данные JSON преобразуются в объекты Club, Topic, Event
  и Registration (метод from_data() каждого класса);
- при сохранении объекты преобразуются в данные методом to_dict().

Объектные ссылки (Registration.event, Event.club, Event.topic) в файлы
не записываются: JSON хранит только идентификаторы event_id, club_id
и topic_id. После загрузки связи восстанавливаются функцией
bind_references().

Данные хранятся в каталоге data рядом с программными модулями. Файлы
создаются при первом запуске программы, поэтому приложение можно
запустить в чистом репозитории. Чтение и запись выполняются через
контекстный менеджер with: файл закрывается даже при возникновении
ошибки. Ошибки доступа к файлу перехватываются и не приводят к
аварийному завершению программы.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from models import Club, Event, Registration, Topic
from registrations import link_registrations
from utils import logged, parse_date

DATA_DIR = Path(__file__).resolve().parent / "data"

CLUBS_FILE = "clubs.json"
TOPICS_FILE = "topics.json"
EVENTS_FILE = "events.json"
REGISTRATIONS_FILE = "registrations.json"


@logged
def load_json(file_path: Path) -> List[Dict[str, Any]]:
    """Прочитать список записей из JSON-файла.

    Возвращает пустой список, если файл отсутствует, его содержимое не
    является корректным JSON или JSON содержит не список. Приложение
    при этом продолжает работу: пользователь получает сообщение и пустой
    набор данных вместо трассировки ошибки.
    """
    try:
        with file_path.open(encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f"Файл данных {file_path.name} не найден: набор пуст.")
        return []
    except json.JSONDecodeError as error:
        print(
            f"Файл данных {file_path.name} повреждён ({error.msg}): "
            "набор данных пуст."
        )
        return []
    except OSError as error:
        print(f"Файл данных {file_path.name} недоступен: {error}")
        return []

    if not isinstance(data, list):
        print(
            f"Файл данных {file_path.name} должен содержать список: "
            "набор данных пуст."
        )
        return []
    return [record for record in data if isinstance(record, dict)]


@logged
def save_json(file_path: Path, records: List[Dict[str, Any]]) -> bool:
    """Записать список записей в JSON-файл.

    Возвращает True, если данные сохранены, и False, если запись не
    удалась. Исключение OSError перехватывается внутри функции.
    """
    try:
        with file_path.open("w", encoding="utf-8") as file:
            json.dump(records, file, ensure_ascii=False, indent=2)
            file.write("\n")
    except OSError as error:
        print(f"Не удалось сохранить файл {file_path.name}: {error}")
        return False
    return True


def objects_to_records(objects: List[Any]) -> List[Dict[str, Any]]:
    """Преобразовать коллекцию объектов в список словарей.

    Преобразование выполняется вызовом метода to_dict() каждого объекта:
    объекты не должны храниться в JSON-файле как есть.
    """
    return [item.to_dict() for item in objects]


def records_to_ids(records: List[Dict[str, Any]]) -> List[int]:
    """Получить идентификаторы записей, пропуская записи без них."""
    identifiers = []
    for record in records:
        if "id" in record:
            identifiers.append(int(record["id"]))
    return identifiers


def load_clubs() -> List[Club]:
    """Загрузить клубы из файла data/clubs.json как объекты Club."""
    clubs = []
    for record in load_json(DATA_DIR / CLUBS_FILE):
        try:
            clubs.append(Club.from_data(record))
        except (TypeError, ValueError) as error:
            print(f"Пропущен клуб с неверными данными: {error}")
    return clubs


def save_clubs(clubs: List[Club]) -> bool:
    """Сохранить коллекцию клубов в файл data/clubs.json."""
    return save_json(DATA_DIR / CLUBS_FILE, objects_to_records(clubs))


def load_topics() -> List[Topic]:
    """Загрузить темы из файла data/topics.json как объекты Topic."""
    topics = []
    for record in load_json(DATA_DIR / TOPICS_FILE):
        try:
            topics.append(Topic.from_data(record))
        except (TypeError, ValueError) as error:
            print(f"Пропущена тема с неверными данными: {error}")
    return topics


def save_topics(topics: List[Topic]) -> bool:
    """Сохранить коллекцию тем в файл data/topics.json."""
    return save_json(DATA_DIR / TOPICS_FILE, objects_to_records(topics))


def load_events() -> List[Event]:
    """Загрузить мероприятия из файла data/events.json.

    Объекты создаются методом Event.from_data(): дата из строки
    преобразуется в объект date. Записи с неверной датой пропускаются:
    одно повреждённое значение не должно мешать загрузке остальных
    данных.
    """
    events = []
    for record in load_json(DATA_DIR / EVENTS_FILE):
        try:
            events.append(Event.from_data(record, parse_date=parse_date))
        except (TypeError, ValueError) as error:
            print(f"Пропущено мероприятие с неверной датой: {error}")
    return events


def save_events(events: List[Event]) -> bool:
    """Сохранить коллекцию мероприятий в файл data/events.json."""
    return save_json(DATA_DIR / EVENTS_FILE, objects_to_records(events))


def load_registrations(events: List[Event]) -> List[Registration]:
    """Загрузить регистрации из файла data/registrations.json.

    Связь с мероприятиями восстанавливается после создания объектов:
    каждый объект Registration получает ссылку на объект Event.
    """
    registrations = []
    for record in load_json(DATA_DIR / REGISTRATIONS_FILE):
        try:
            registrations.append(Registration.from_data(record))
        except (TypeError, ValueError) as error:
            print(f"Пропущена регистрация с неверными данными: {error}")
    link_registrations(registrations, events)
    return registrations


def save_registrations(registrations: List[Registration]) -> bool:
    """Сохранить коллекцию регистраций в registrations.json."""
    return save_json(
        DATA_DIR / REGISTRATIONS_FILE, objects_to_records(registrations)
    )


def bind_references(clubs: List[Club], topics: List[Topic],
                    events: List[Event],
                    registrations: List[Registration]) -> None:
    """Связать объекты предметной области друг с другом.

    Мероприятие получает ссылки на свой клуб и тему, регистрация — на
    своё мероприятие. В коллекциях остаются те же объекты: копий не
    создаётся, поэтому изменение объекта видно всем его пользователям.
    """
    clubs_by_id = {club.id: club for club in clubs}
    topics_by_id = {topic.id: topic for topic in topics}
    for event in events:
        event.link(club=clubs_by_id.get(event.club_id),
                   topic=topics_by_id.get(event.topic_id))
    link_registrations(registrations, events)


def load_project() -> Tuple[List[Club], List[Topic], List[Event],
                            List[Registration]]:
    """Загрузить все коллекции проекта одной командой.

    Возвращает кортеж: клубы, темы, мероприятия, регистрации — все
    уже готовые объекты со связями между собой.
    """
    clubs = load_clubs()
    topics = load_topics()
    events = load_events()
    registrations = load_registrations(events)
    bind_references(clubs, topics, events, registrations)
    return clubs, topics, events, registrations


def save_project(clubs: List[Club], topics: List[Topic],
                 events: List[Event],
                 registrations: List[Registration]) -> bool:
    """Сохранить все коллекции проекта одной командой.

    Возвращает True, если все файлы записаны успешно.
    """
    results = [
        save_clubs(clubs),
        save_topics(topics),
        save_events(events),
        save_registrations(registrations),
    ]
    return all(results)


def init_project(clubs: List[Club], topics: List[Topic],
                 events: List[Event],
                 registrations: List[Registration]) -> None:
    """Создать каталог data и записать в него начальные данные.

    Функция вызывается при первом запуске программы, когда файлы
    данных ещё отсутствуют.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    save_project(clubs, topics, events, registrations)
