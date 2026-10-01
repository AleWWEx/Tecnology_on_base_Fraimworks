"""Тесты утилитарных функций."""

import datetime

from utils import (
    DATE_FORMAT_HINT,
    format_date,
    input_choice,
    input_int,
    input_text,
    next_id,
    parse_date,
    parse_user_date,
)


def test_input_text_rejects_empty(monkeypatch, capsys):
    answers = ["", "  ", "Тест"]
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": answers.pop(0) if answers else "",
    )

    result = input_text("Введите: ")

    assert result == "Тест"
    captured = capsys.readouterr()
    assert "Ошибка ввода" in captured.out


def test_input_int_accepts_integer(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "123")

    assert input_int("Введите число: ") == 123


def test_input_int_retries_on_invalid(monkeypatch, capsys):
    answers = ["abc", "12.5", "25"]
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": answers.pop(0) if answers else "",
    )

    assert input_int("Введите число: ") == 25
    assert "Ошибка ввода" in capsys.readouterr().out


def test_input_choice_normalizes_case(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "Да")

    assert input_choice("Выберите", ("да", "нет")) == "да"


def test_input_choice_retries_on_invalid(monkeypatch):
    answers = ["maybe", "нет"]
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt="": answers.pop(0) if answers else "",
    )

    assert input_choice("Выберите", ("да", "нет")) == "нет"


def test_parse_user_date_returns_date():
    date = parse_user_date("15.10.2026")

    assert date == datetime.date(2026, 10, 15)


def test_parse_user_date_raises_on_invalid():
    try:
        parse_user_date("2026-10-15")
        assert False
    except ValueError:
        pass


def test_parse_date_handles_iso_format():
    assert parse_date("2026-10-15") == datetime.date(2026, 10, 15)


def test_format_date_formats_to_dd_mm_yyyy():
    assert format_date(datetime.date(2026, 10, 15)) == "15.10.2026"


def test_next_id_returns_one_for_empty_dict():
    assert next_id({}) == 1


def test_next_id_returns_max_plus_one():
    assert next_id({1: {}, 5: {}, 3: {}}) == 6


def test_date_format_hint_is_correct():
    assert DATE_FORMAT_HINT == "ДД.ММ.ГГГГ"
