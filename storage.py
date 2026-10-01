"""Сохранение и загрузка данных проекта в JSON-файлах.

Данные хранятся в каталоге data рядом с программными модулями. Файлы
создаются при первом запуске программы, поэтому приложение можно
запустить в чистом репозитории.

Чтение и запись выполняются через контекстный менеджер with: файл
закрывается даже при возникновении ошибки. Ошибки доступа к файлу
перехватываются и не приводят к аварийному завершению программы.
"""

import datetime
import json
from pathlib import Path

from utils import STORAGE_DATE_FORMAT

DATA_DIR = Path(__file__).resolve().parent / "data"

CLUBS_FILE = "clubs.json"
TOPICS_FILE = "topics.json"
EVENTS_FILE = "events.json"
REGISTRATIONS_FILE = "registrations.json"


def load_json(file_path: Path) -> list[dict]:
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


def save_json(file_path: Path, records: list[dict]) -> bool:
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


def records_to_dict(records: list[dict]) -> dict[int, dict]:
    """Преобразовать список записей в словарь по идентификатору.

    Записи без идентификатора пропускаются: без него запись нельзя
    адресовать в словаре.
    """
    items: dict[int, dict] = {}
    for record in records:
        if "id" not in record:
            continue
        items[int(record["id"])] = record
    return items


def dict_to_records(items: dict[int, dict]) -> list[dict]:
    """Преобразовать словарь записей в список для сохранения."""
    return list(items.values())


def prepare_event(record: dict) -> dict:
    """Привести запись мероприятия к виду, удобному для работы.

    Дата преобразуется из строки в объект date: сравнение дат в
    модуле events.py выполняется над объектами.
    """
    prepared = dict(record)
    if "event_date" in prepared:
        prepared["event_date"] = datetime.datetime.strptime(
            str(prepared["event_date"]), STORAGE_DATE_FORMAT
        ).date()
    return prepared


def load_clubs() -> dict[int, dict]:
    """Загрузить клубы из файла data/clubs.json."""
    return records_to_dict(load_json(DATA_DIR / CLUBS_FILE))


def save_clubs(clubs: dict[int, dict]) -> bool:
    """Сохранить клубы в файл data/clubs.json."""
    return save_json(DATA_DIR / CLUBS_FILE, dict_to_records(clubs))


def load_topics() -> dict[int, dict]:
    """Загрузить темы дискуссий из файла data/topics.json."""
    return records_to_dict(load_json(DATA_DIR / TOPICS_FILE))


def save_topics(topics: dict[int, dict]) -> bool:
    """Сохранить темы дискуссий в файл data/topics.json."""
    return save_json(DATA_DIR / TOPICS_FILE, dict_to_records(topics))


def load_events() -> dict[int, dict]:
    """Загрузить мероприятия из файла data/events.json.

    Записи, у которых дата записана неверно, пропускаются: одно
    повреждённое значение не должно мешать загрузке остальных данных.
    """
    records = load_json(DATA_DIR / EVENTS_FILE)
    events: dict[int, dict] = {}
    for record in records:
        try:
            prepared = prepare_event(record)
        except (ValueError, TypeError):
            print(f"Пропущено мероприятие с неверной датой: {record}")
            continue
        events[int(prepared["id"])] = prepared
    return events


def save_events(events: dict[int, dict]) -> bool:
    """Сохранить мероприятия в файл data/events.json."""
    records = []
    for record in events.values():
        item = dict(record)
        item["event_date"] = item["event_date"].strftime(STORAGE_DATE_FORMAT)
        records.append(item)
    return save_json(DATA_DIR / EVENTS_FILE, records)


def load_registrations() -> list[dict]:
    """Загрузить регистрации из файла data/registrations.json."""
    return load_json(DATA_DIR / REGISTRATIONS_FILE)


def save_registrations(registrations: list[dict]) -> bool:
    """Сохранить регистрации в файл data/registrations.json."""
    return save_json(DATA_DIR / REGISTRATIONS_FILE, registrations)


def load_project() -> tuple[dict[int, dict], dict[int, dict],
                            dict[int, dict], list[dict]]:
    """Загрузить все коллекции проекта одной командой.

    Возвращает кортеж: клубы, темы, мероприятия, регистрации.
    """
    return (
        load_clubs(),
        load_topics(),
        load_events(),
        load_registrations(),
    )


def save_project(clubs: dict[int, dict], topics: dict[int, dict],
                 events: dict[int, dict],
                 registrations: list[dict]) -> bool:
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


def init_project(clubs: dict[int, dict], topics: dict[int, dict],
                 events: dict[int, dict],
                 registrations: list[dict]) -> None:
    """Создать каталог data и записать в него начальные данные.

    Функция вызывается при первом запуске программы, когда файлы
    данных ещё отсутствуют.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    save_project(clubs, topics, events, registrations)
