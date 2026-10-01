"""Тесты функций работы с регистрациями."""

import datetime

from events import (
    PLACEHOLDING_STATUSES,
    STATUS_ATTENDED,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_FINISHED,
    STATUS_PENDING,
    STATUS_PLANNED,
    count_active_registrations,
    count_registrations_by_status,
)
from registrations import (
    RESULT_APPROVED,
    RESULT_REJECTED,
    RESULT_WAITING,
    cancel_registration,
    check_requirements,
    confirm_registration,
    create_registration,
    find_registrations_by_name,
    generate_ticket_code,
    get_availability_text,
    get_registration_card,
    get_registration_result,
    is_event_available,
    next_registration_id,
)


def test_check_requirements_all_met():
    assert check_requirements(19, "средний", True, 16, "средний") == ""


def test_check_requirements_too_young():
    reason = check_requirements(15, "средний", True, 16, "средний")

    assert "15" in reason
    assert "16" in reason


def test_check_requirements_materials_not_read():
    reason = check_requirements(19, "средний", False, 16, "средний")

    assert "материалы" in reason


def test_check_requirements_wrong_level():
    reason = check_requirements(19, "начинающий", True, 16, "средний")

    assert "средний" in reason


def test_get_registration_result_finished_event():
    result, reason = get_registration_result(
        19, "средний", True, STATUS_FINISHED, 5, 16, "средний",
    )

    assert result == RESULT_REJECTED
    assert "завершено" in reason


def test_get_registration_result_rejected_on_requirements():
    result, _ = get_registration_result(
        14, "средний", True, STATUS_PLANNED, 5, 16, "средний",
    )

    assert result == RESULT_REJECTED


def test_get_registration_result_waiting_no_places():
    result, reason = get_registration_result(
        19, "средний", True, STATUS_PLANNED, 0, 16, "средний",
    )

    assert result == RESULT_WAITING
    assert "мест" in reason


def test_get_registration_result_waiting_priority():
    result, reason = get_registration_result(
        17, "средний", True, STATUS_PLANNED, 1, 16, "средний",
    )

    assert result == RESULT_WAITING
    assert "приоритет" in reason


def test_get_registration_result_approved():
    result, _ = get_registration_result(
        19, "средний", True, STATUS_PLANNED, 2, 16, "средний",
    )

    assert result == RESULT_APPROVED


def test_generate_ticket_code_format():
    code = generate_ticket_code()

    assert code.startswith("DC-")
    assert len(code) == 7
    assert code[3:].isdigit()


def test_count_active_registrations_excludes_pending_and_cancelled():
    registrations = [
        {"event_id": 1, "status": STATUS_PENDING},
        {"event_id": 1, "status": STATUS_CONFIRMED},
        {"event_id": 1, "status": STATUS_ATTENDED},
        {"event_id": 1, "status": STATUS_CANCELLED},
    ]

    assert count_active_registrations(registrations, 1) == 2


def test_is_event_available_when_free_and_not_finished(event, registrations):
    available = is_event_available({1: event[1]}, registrations, 1)

    assert available is True


def test_is_event_available_returns_false_when_full(event, registrations):
    event[1]["capacity"] = 2
    create_registration(
        registrations, 1, "А", 19, "средний", True, STATUS_CONFIRMED
    )
    create_registration(
        registrations, 1, "Б", 19, "средний", True, STATUS_CONFIRMED
    )

    assert is_event_available({1: event[1]}, registrations, 1) is False


def test_is_event_available_returns_false_when_finished(event, registrations):
    event[1]["event_date"] = datetime.date(2026, 9, 1)
    assert is_event_available(
        {1: event[1]}, registrations, 1, datetime.date(2026, 10, 1)
    ) is False


def test_create_registration_adds_record():
    registrations = []

    record = create_registration(
        registrations, 1, "Мария", 19, "средний", True
    )

    assert len(registrations) == 1
    assert record["status"] == STATUS_PENDING
    assert record["ticket_code"].startswith("DC-")


def test_create_registration_allows_custom_status():
    registrations = []

    record = create_registration(
        registrations, 1, "Мария", 19, "средний", True, STATUS_CONFIRMED
    )

    assert record["status"] == STATUS_CONFIRMED


def test_next_registration_id_handles_empty_list():
    assert next_registration_id([]) == 1


def test_next_registration_id_uses_max():
    registrations = [
        {"id": 1},
        {"id": 5},
        {"id": 3},
    ]

    assert next_registration_id(registrations) == 6


def test_cancel_registration_marks_as_cancelled():
    registrations = []

    record = create_registration(
        registrations, 1, "Мария", 19, "средний", True, STATUS_CONFIRMED
    )

    assert cancel_registration(registrations, record["id"]) is True
    assert registrations[0]["status"] == STATUS_CANCELLED


def test_cancel_registration_returns_false_for_missing():
    assert cancel_registration([], 1) is False


def test_confirm_registration_changes_pending_to_confirmed():
    registrations = []
    record = create_registration(
        registrations, 1, "Мария", 19, "средний", True
    )

    assert confirm_registration(registrations, record["id"]) is True
    assert registrations[0]["status"] == STATUS_CONFIRMED


def test_confirm_registration_does_not_change_other_statuses():
    registrations = []
    confirmed = create_registration(
        registrations, 1, "Мария", 19, "средний", True, STATUS_CONFIRMED
    )
    cancelled = create_registration(
        registrations, 1, "Ольга", 17, "средний", True, STATUS_CANCELLED
    )

    assert confirm_registration(registrations, confirmed["id"]) is False
    assert confirm_registration(registrations, cancelled["id"]) is False


def test_find_registrations_by_name_ignores_case():
    registrations = []
    create_registration(registrations, 1, "Мария К.", 19, "средний", True)

    assert find_registrations_by_name(registrations, "мария") == [1]


def test_find_registrations_by_name_returns_empty():
    assert find_registrations_by_name([], "никто") == []


def test_count_registrations_by_status():
    registrations = [
        {"event_id": 1, "status": STATUS_PENDING},
        {"event_id": 1, "status": STATUS_PENDING},
        {"event_id": 2, "status": STATUS_PENDING},
    ]

    assert count_registrations_by_status(registrations, 1, STATUS_PENDING) == 2


def test_get_availability_text():
    assert "доступно" in get_availability_text(True).lower()
    assert "недоступно" in get_availability_text(False).lower()


def test_get_registration_card_contains_data(event):
    record = {
        "name": "Мария К.",
        "age": 19,
        "level": "средний",
        "has_read_materials": True,
        "status": STATUS_CONFIRMED,
        "ticket_code": "DC-4821",
        "event_id": 1,
    }

    card = get_registration_card(record, event[1])

    assert "Мария К." in card
    assert "DC-4821" in card


def test_status_sets_contain_required_values():
    assert STATUS_CONFIRMED in PLACEHOLDING_STATUSES
    assert STATUS_ATTENDED in PLACEHOLDING_STATUSES
    assert STATUS_PENDING not in PLACEHOLDING_STATUSES
    assert STATUS_CANCELLED not in PLACEHOLDING_STATUSES
