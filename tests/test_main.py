"""Тесты начального сценария «Запись на мероприятие клуба»."""

import datetime

from main import (
    CAPACITY,
    EVENT_TITLE,
    MIN_AGE,
    REQUIRED_LEVEL,
    RESULT_APPROVED,
    RESULT_REJECTED,
    RESULT_WAITING,
    STATUS_FINISHED,
    STATUS_PLANNED,
    STATUS_RUNNING,
    check_requirements,
    generate_ticket_code,
    get_event_card,
    get_event_status,
    get_free_places,
    get_registration_result,
)

TODAY = datetime.date(2026, 10, 1)


def test_event_is_planned_before_date():
    assert get_event_status(TODAY, TODAY) == STATUS_RUNNING
    assert get_event_status(TODAY.replace(day=15), TODAY) == STATUS_PLANNED


def test_event_is_finished_after_date():
    tomorrow = TODAY.replace(day=2)

    assert get_event_status(TODAY, tomorrow) == STATUS_FINISHED


def test_free_places_never_negative():
    assert get_free_places(23, CAPACITY) == 2
    assert get_free_places(CAPACITY, CAPACITY) == 0
    assert get_free_places(CAPACITY + 5, CAPACITY) == 0


def test_requirements_met():
    reason = check_requirements(19, REQUIRED_LEVEL, True)

    assert reason == ""


def test_requirements_too_young():
    reason = check_requirements(MIN_AGE - 1, REQUIRED_LEVEL, True)

    assert str(MIN_AGE - 1) in reason


def test_requirements_materials_not_read():
    reason = check_requirements(19, REQUIRED_LEVEL, False)

    assert "материалы" in reason


def test_requirements_wrong_level():
    reason = check_requirements(19, "новичок", True)

    assert REQUIRED_LEVEL in reason


def test_finished_event_is_rejected():
    result, reason = get_registration_result(
        19, REQUIRED_LEVEL, True, STATUS_FINISHED, 5
    )

    assert result == RESULT_REJECTED
    assert "завершено" in reason


def test_failed_requirements_are_rejected():
    result, _ = get_registration_result(
        14, REQUIRED_LEVEL, True, STATUS_PLANNED, 5
    )

    assert result == RESULT_REJECTED


def test_no_places_goes_to_waiting_list():
    result, reason = get_registration_result(
        19, REQUIRED_LEVEL, True, STATUS_PLANNED, 0
    )

    assert result == RESULT_WAITING
    assert "мест" in reason


def test_minor_goes_to_waiting_list_on_last_places():
    result, _ = get_registration_result(
        17, REQUIRED_LEVEL, True, STATUS_PLANNED, 1
    )

    assert result == RESULT_WAITING


def test_application_is_approved():
    result, _ = get_registration_result(
        19, REQUIRED_LEVEL, True, STATUS_PLANNED, 2
    )

    assert result == RESULT_APPROVED


def test_ticket_code_format():
    code = generate_ticket_code()

    assert code.startswith("DC-")
    assert len(code) == 7
    assert code[3:].isdigit()


def test_event_card_contains_key_data():
    card = get_event_card(23, 2, STATUS_PLANNED)

    assert EVENT_TITLE in card
    assert "свободно 2" in card
    assert STATUS_PLANNED in card
