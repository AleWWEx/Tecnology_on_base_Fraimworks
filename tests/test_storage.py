"""Тесты функций работы с хранилищем данных."""

import datetime
import json

import storage


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


def test_records_to_dict_builds_dict_by_id():
    records = [
        {"id": 1, "name": "Первый"},
        {"id": 5, "name": "Пятый"},
        {"value": 0},
    ]

    result = storage.records_to_dict(records)

    assert result == {
        1: {"id": 1, "name": "Первый"},
        5: {"id": 5, "name": "Пятый"},
    }


def test_dict_to_records_returns_list():
    items = {1: {"id": 1, "name": "Тест"}}

    assert storage.dict_to_records(items) == [{"id": 1, "name": "Тест"}]


def test_prepare_event_converts_date():
    prepared = storage.prepare_event({"id": 1, "event_date": "2026-10-15"})

    assert prepared["event_date"] == datetime.date(2026, 10, 15)


def test_prepare_event_keeps_other_fields():
    prepared = storage.prepare_event({"id": 1, "capacity": 25})

    assert prepared["capacity"] == 25


def test_load_project_after_save_project(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    clubs = {1: make_club()}
    topics = {1: make_topic()}
    events = {1: make_event()}
    registrations = [make_registration()]

    saved = storage.save_project(clubs, topics, events, registrations)
    loaded_clubs, loaded_topics, loaded_events, loaded_regs = (
        storage.load_project()
    )

    assert saved is True
    assert loaded_clubs == clubs
    assert loaded_topics == topics
    assert loaded_events[1]["event_date"] == datetime.date(2026, 10, 15)
    assert loaded_regs == registrations


def test_save_events_converts_date_to_string(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    events = {1: make_event()}

    storage.save_events(events)
    saved = json.loads(
        (tmp_path / storage.EVENTS_FILE).read_text(encoding="utf-8")
    )

    assert saved[0]["event_date"] == "2026-10-15"


def test_load_events_skips_record_with_bad_date(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path)
    path = tmp_path / storage.EVENTS_FILE
    path.write_text(
        '[{"id": 1, "event_date": "не дата"},'
        ' {"id": 2, "event_date": "2026-10-15"}]\n',
        encoding="utf-8",
    )

    events = storage.load_events()

    assert list(events) == [2]


def test_init_project_creates_data_dir(tmp_path, monkeypatch):
    target = tmp_path / "nested" / "data"
    monkeypatch.setattr(storage, "DATA_DIR", target)

    storage.init_project({}, {}, {}, [])

    assert target.exists()
    assert (target / storage.CLUBS_FILE).exists()


def make_club():
    """Собрать тестовую запись клуба."""
    return {
        "id": 1,
        "name": "Клуб",
        "description": "Описание",
        "moderator": "Модератор",
    }


def make_topic():
    """Собрать тестовую запись темы дискуссии."""
    return {
        "id": 1,
        "title": "Тема",
        "level": "средний",
        "tags": ["этика"],
        "materials": "Материалы",
    }


def make_event():
    """Собрать тестовую запись мероприятия."""
    return {
        "id": 1,
        "club_id": 1,
        "topic_id": 1,
        "event_date": datetime.date(2026, 10, 15),
        "start_time": "18:30",
        "format": "онлайн",
        "place": "ссылка на комнату",
        "capacity": 25,
        "min_age": 16,
        "required_level": "средний",
    }


def make_registration():
    """Собрать тестовую запись регистрации."""
    return {
        "id": 1,
        "event_id": 1,
        "name": "Мария К.",
        "age": 19,
        "level": "средний",
        "has_read_materials": True,
        "status": "подтверждён",
        "ticket_code": "DC-1001",
    }
