"""Тесты функций работы с хранилищем данных.

Проверяется преобразование данных JSON в объекты и объектов обратно
в данные, а также восстановление связей между объектами.
"""

import datetime
import json

import storage
from models import Club, Event, Registration, Topic


def test_load_json_returns_empty_list_when_file_missing(tmp_path):
    path = tmp_path / "data.json"

    assert storage.load_json(path) == []


def test_load_json_returns_empty_list_when_not_list(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("{}", encoding="utf-8")

    assert storage.load_json(path) == []


def test_load_json_returns_empty_list_when_corrupted(tmp_path):
    path = tmp_path / "data.json"
    path.write_text("{", encoding="utf-8")

    assert storage.load_json(path) == []


def test_load_json_reads_list(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('[{"id": 1, "name": "Тест"}]\n', encoding="utf-8")

    assert storage.load_json(path) == [{"id": 1, "name": "Тест"}]


def test_load_json_skips_non_dict_items(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('[{"id": 1}, 5, "текст"]\n', encoding="utf-8")

    assert storage.load_json(path) == [{"id": 1}]


def test_save_json_writes_file(tmp_path):
    path = tmp_path / "data.json"
    records = [{"id": 1, "name": "Тест"}]

    assert storage.save_json(path, records) is True
    content = json.loads(path.read_text(encoding="utf-8"))
    assert content == records


def test_save_json_returns_false_on_os_error(tmp_path, monkeypatch):
    path = tmp_path / "data.json"

    def raise_error(self, *args, **kwargs):
        raise OSError("нет доступа")

    monkeypatch.setattr("pathlib.Path.open", raise_error)

    assert storage.save_json(path, []) is False


def test_objects_to_records_uses_to_dict():
    objects = [make_club(), make_topic()]

    records = storage.objects_to_records(objects)

    assert records[0]["name"] == "Клуб"
    assert records[1]["title"] == "Тема"


def test_records_to_ids_skips_records_without_id():
    records = [{"id": 1}, {"value": 0}, {"id": 5}]

    assert storage.records_to_ids(records) == [1, 5]


def test_save_and_load_clubs(data_dir):
    clubs = [make_club()]

    storage.save_clubs(clubs)
    loaded = storage.load_clubs()

    assert isinstance(loaded[0], Club)
    assert loaded[0].name == "Клуб"
    assert loaded[0].moderator == "Модератор"


def test_save_and_load_topics(data_dir):
    storage.save_topics([make_topic()])

    loaded = storage.load_topics()

    assert isinstance(loaded[0], Topic)
    assert list(loaded[0].tags) == ["этика"]


def test_save_events_converts_date_to_string(data_dir):
    storage.save_events([make_event()])
    saved = json.loads(
        (data_dir / storage.EVENTS_FILE).read_text(encoding="utf-8")
    )

    assert saved[0]["event_date"] == "2026-10-15"


def test_load_events_returns_objects_with_dates(data_dir):
    storage.save_events([make_event()])

    loaded = storage.load_events()

    assert isinstance(loaded[0], Event)
    assert loaded[0].event_date == datetime.date(2026, 10, 15)


def test_load_events_skips_record_with_bad_date(data_dir):
    path = data_dir / storage.EVENTS_FILE
    path.write_text(
        '[{"id": 1, "event_date": "не дата"},'
        ' {"id": 2, "event_date": "2026-10-15"}]\n',
        encoding="utf-8",
    )

    events = storage.load_events()

    assert [item.id for item in events] == [2]


def test_save_and_load_registrations(data_dir):
    storage.save_events([make_event()])
    storage.save_registrations([make_registration()])

    loaded = storage.load_registrations(storage.load_events())

    assert isinstance(loaded[0], Registration)
    assert loaded[0].name == "Мария К."
    assert loaded[0].ticket_code == "DC-1001"


def test_load_registrations_restores_event_link(data_dir):
    storage.save_events([make_event()])
    storage.save_registrations([make_registration()])

    loaded = storage.load_registrations(storage.load_events())

    assert loaded[0].event is not None
    assert loaded[0].event.id == 1


def test_saved_json_has_no_objects(data_dir):
    storage.save_events([make_event()])
    storage.save_registrations([make_registration()])

    events_text = (data_dir / storage.EVENTS_FILE).read_text(
        encoding="utf-8"
    )
    regs_text = (data_dir / storage.REGISTRATIONS_FILE).read_text(
        encoding="utf-8"
    )

    assert "Event(" not in events_text
    assert "Registration(" not in regs_text
    assert "event\":" not in regs_text


def test_bind_references_links_objects(data_dir):
    clubs = [make_club()]
    topics = [make_topic()]
    events = [make_event()]
    registrations = [make_registration()]
    for event in events:
        event.link()
    for registration in registrations:
        registration.event = None

    storage.bind_references(clubs, topics, events, registrations)

    assert events[0].club is clubs[0]
    assert events[0].topic is topics[0]
    assert registrations[0].event is events[0]


def test_bind_references_ignores_unknown_links(data_dir):
    events = [make_event()]
    events[0].link()

    storage.bind_references([], [], events, [])

    assert events[0].club is None
    assert events[0].topic is None


def test_load_project_after_save_project(data_dir):
    clubs = [make_club()]
    topics = [make_topic()]
    events = [make_event()]
    registrations = [make_registration()]

    saved = storage.save_project(clubs, topics, events, registrations)
    loaded_clubs, loaded_topics, loaded_events, loaded_regs = (
        storage.load_project()
    )

    assert saved is True
    assert loaded_clubs == clubs
    assert loaded_topics == topics
    assert loaded_events[0].event_date == datetime.date(2026, 10, 15)
    assert loaded_regs == registrations


def test_load_project_creates_links(data_dir):
    storage.save_project(
        [make_club()], [make_topic()], [make_event()], [make_registration()]
    )

    _, _, events, registrations = storage.load_project()

    assert events[0].club is not None
    assert registrations[0].event is events[0]


def test_init_project_creates_data_dir(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "data"
    monkeypatch.setattr(storage, "DATA_DIR", target)

    storage.init_project([], [], [], [])

    assert target.exists()
    assert (target / storage.CLUBS_FILE).exists()


def test_load_functions_log_calls(data_dir):
    from utils import clear_call_log, get_call_log

    clear_call_log()
    storage.load_clubs()

    assert get_call_log() == ["load_json"]
    clear_call_log()


def make_club():
    """Создать объект клуба для теста."""
    return Club(1, "Клуб", "Описание", "Модератор")


def make_topic():
    """Создать объект темы для теста."""
    return Topic(1, "Тема", "средний", ["этика"], "Материалы")


def make_event():
    """Создать объект мероприятия для теста."""
    return Event(1, 1, 1, datetime.date(2026, 10, 15), "18:30", "онлайн",
                 "ссылка на комнату", 25, 16, "средний")


def make_registration():
    """Создать объект регистрации для теста."""
    return Registration(1, 1, "Мария К.", 19, "средний", True,
                        "подтверждён", "DC-1001")
