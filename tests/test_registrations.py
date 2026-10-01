"""Тесты функций и методов работы с регистрациями."""

import datetime

from models import Registration
from registrations import (
    MIN_PRIORITY_AGE,
    PRIORITY_FREE_PLACES,
    RESULT_APPROVED,
    RESULT_REJECTED,
    RESULT_WAITING,
    cancel_registration,
    check_requirements,
    confirm_registration,
    create_registration,
    filter_registrations_by_status,
    find_registrations_by_name,
    generate_ticket_code,
    get_availability_text,
    get_registration,
    get_registration_card,
    get_registration_result,
    is_event_available,
    link_registrations,
    next_registration_id,
)
from events import (
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_FINISHED,
    STATUS_PENDING,
)

TODAY = datetime.date(2026, 10, 1)


def test_check_requirements_returns_empty_when_ok():
    assert check_requirements(19, "средний", True, 16, "средний") == ""


def test_check_requirements_age():
    reason = check_requirements(14, "средний", True, 16, "средний")

    assert "возраст" in reason


def test_check_requirements_materials():
    reason = check_requirements(19, "средний", False, 16, "средний")

    assert "материалы" in reason


def test_check_requirements_level():
    reason = check_requirements(19, "начинающий", True, 16, "средний")

    assert "уровень" in reason


def test_registration_result_rejects_finished_event():
    result, reason = get_registration_result(
        19, "средний", True, STATUS_FINISHED, 5, 16, "средний"
    )

    assert result == RESULT_REJECTED
    assert reason == "мероприятие уже завершено"


def test_registration_result_rejects_bad_age():
    result, _ = get_registration_result(
        14, "средний", True, "планируется", 5, 16, "средний"
    )

    assert result == RESULT_REJECTED


def test_registration_result_waits_without_free_places():
    result, reason = get_registration_result(
        19, "средний", True, "планируется", 0, 16, "средний"
    )

    assert result == RESULT_WAITING
    assert reason == "свободных мест нет"


def test_registration_result_waits_by_priority():
    result, reason = get_registration_result(
        17, "средний", True, "планируется", 1, 16, "средний"
    )

    assert result == RESULT_WAITING
    assert "приоритет" in reason


def test_registration_result_approves():
    result, _ = get_registration_result(
        19, "средний", True, "планируется", 2, 16, "средний"
    )

    assert result == RESULT_APPROVED


def test_priority_constants():
    assert MIN_PRIORITY_AGE == 18
    assert PRIORITY_FREE_PLACES == 3


def test_generate_ticket_code_format():
    code = generate_ticket_code()

    assert code.startswith("DC-")
    assert len(code) == 7


def test_get_availability_text():
    assert "доступно" in get_availability_text(True)
    assert "недоступно" in get_availability_text(False)


def test_create_registration_creates_object(registrations):
    registration = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True, STATUS_CONFIRMED
    )

    assert isinstance(registration, Registration)
    assert registration.id == 1
    assert registrations == [registration]


def test_create_registration_default_status_is_pending(registrations):
    registration = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True
    )

    assert registration.status == STATUS_PENDING


def test_next_registration_id_increments(registrations):
    create_registration(registrations, 1, "Первый", 19, "средний", True)

    assert next_registration_id(registrations) == 2


def test_next_registration_id_for_empty_collection(registrations):
    assert next_registration_id(registrations) == 1


def test_get_registration_returns_object(registrations):
    registration = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True
    )

    assert get_registration(registrations, registration.id) is registration


def test_get_registration_returns_none_when_missing(registrations):
    assert get_registration(registrations, 99) is None


def test_cancel_registration_changes_state(registrations):
    registration = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True, STATUS_CONFIRMED
    )

    assert cancel_registration(registrations, registration.id) is True
    assert registration.status == STATUS_CANCELLED


def test_cancel_registration_keeps_object_in_collection(registrations):
    registration = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True, STATUS_CONFIRMED
    )

    cancel_registration(registrations, registration.id)

    assert len(registrations) == 1


def test_cancel_registration_returns_false_when_missing(registrations):
    assert cancel_registration(registrations, 42) is False


def test_cancel_registration_twice(registrations):
    registration = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True, STATUS_CONFIRMED
    )

    cancel_registration(registrations, registration.id)

    assert cancel_registration(registrations, registration.id) is True


def test_confirm_registration_changes_state(registrations):
    registration = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True
    )

    assert confirm_registration(registrations, registration.id) is True
    assert registration.status == STATUS_CONFIRMED


def test_confirm_registration_rejects_confirmed(registrations):
    registration = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True, STATUS_CONFIRMED
    )

    assert confirm_registration(registrations, registration.id) is False


def test_confirm_registration_rejects_cancelled(registrations):
    registration = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True, STATUS_CANCELLED
    )

    assert confirm_registration(registrations, registration.id) is False


def test_confirm_registration_returns_false_when_missing(registrations):
    assert confirm_registration(registrations, 7) is False


def test_find_registrations_by_name_ignores_case(registrations):
    create_registration(registrations, 1, "Мария К.", 19, "средний", True)
    create_registration(registrations, 1, "Иван П.", 19, "средний", True)

    found = find_registrations_by_name(registrations, "мария")

    assert [item.name for item in found] == ["Мария К."]


def test_find_registrations_by_partial_name(registrations):
    create_registration(registrations, 1, "Мария К.", 19, "средний", True)

    assert len(find_registrations_by_name(registrations, "р")) == 1


def test_filter_registrations_by_status(registrations):
    create_registration(registrations, 1, "Первый", 19, "средний", True)
    create_registration(
        registrations, 1, "Второй", 19, "средний", True, STATUS_CONFIRMED
    )

    found = filter_registrations_by_status(registrations, STATUS_CONFIRMED)

    assert [item.name for item in found] == ["Второй"]


def test_is_event_available_true(event, registrations_of_event):
    assert is_event_available(
        event, registrations_of_event, 1, TODAY
    ) is True


def test_is_event_available_false_when_full(event, registrations):
    for number in range(25):
        create_registration(
            registrations, 1, f"Участник {number}", 19, "средний", True,
            STATUS_CONFIRMED,
        )

    assert is_event_available(event, registrations, 1, TODAY) is False


def test_is_event_available_false_when_finished(event, registrations):
    event[0].event_date = datetime.date(2026, 9, 1)

    assert is_event_available(event, registrations, 1, TODAY) is False


def test_is_event_available_false_when_missing(events, registrations):
    assert is_event_available(events, registrations, 1, TODAY) is False


def test_get_registration_card_uses_event(registrations, event):
    registration = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True, STATUS_CONFIRMED
    )
    registration.link(event[0])

    card = get_registration_card(registration)

    assert "Мария К." in card
    assert "15.10.2026" in card
    assert STATUS_CONFIRMED in card


def test_link_registrations_attaches_events(registrations, event):
    registration = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True
    )

    link_registrations(registrations, event)

    assert registration.event is event[0]


def test_link_registrations_ignores_unknown_event(registrations):
    registration = create_registration(
        registrations, 99, "Мария К.", 19, "средний", True
    )

    link_registrations(registrations, [])

    assert registration.event is None
