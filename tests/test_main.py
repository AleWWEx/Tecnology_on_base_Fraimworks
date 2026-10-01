"""Тесты функций основного модуля приложения.

Проверяются обработка заявки участника, функции вывода и обработчики
меню. Данные проекта хранятся во временном каталоге: файлы репозитория
тесты не изменяют.
"""

import datetime

import pytest

import analytics
import clubs
import events
import main
import registrations
import storage
import topics
from clubs import add_club
from events import STATUS_CONFIRMED, STATUS_PENDING, add_event
from main import (
    DEMO_EVENT_ID,
    RESULT_APPROVED,
    RESULT_REJECTED,
    RESULT_WAITING,
    add_club_from_input,
    add_event_from_input,
    add_topic_from_input,
    cancel_registration_by_name,
    check_availability,
    confirm_registration_by_id,
    find_and_show_club,
    find_and_show_topic,
    input_event_id,
    main as main_entry,
    print_event_card,
    process_application,
    register_participant,
    run_demo,
    run_introspection,
    run_menu,
    run_mode,
    show_clubs,
    show_registrations,
    show_statistics,
    show_topics,
    show_upcoming_events,
)
from registrations import create_registration
from topics import add_topic

TODAY = datetime.date(2026, 10, 1)


def make_project(clubs_data, topics_data, events_data, registrations_data):
    """Заполнить коллекции данными для проверки меню."""
    add_club(clubs_data, "Философский клуб", "Описание клуба", "Модератор")
    add_topic(topics_data, "Справедливость", "средний", ["этика"],
              "Материалы")
    add_event(
        events_data, 1, 1, datetime.date(2026, 10, 15), "18:30", "онлайн",
        "ссылка на комнату", 25, 16, "средний",
    )
    add_event(
        events_data, 1, 1, datetime.date(2026, 9, 1), "18:30", "офлайн",
        "Зал клуба", 10, 16, "средний",
    )
    return events_data


def make_event_record():
    """Вернуть данные мероприятия для проверки обработки заявки."""
    return {
        "id": DEMO_EVENT_ID,
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


def test_process_application_approves_and_saves(registrations):
    result = process_application(
        registrations, make_event_record(), "Мария К.", "19", "средний",
        "да", TODAY,
    )

    assert result == RESULT_APPROVED
    assert len(registrations) == 1
    assert registrations[0]["status"] == STATUS_CONFIRMED
    assert registrations[0]["name"] == "Мария К."


def test_process_application_prints_ticket_code(registrations, capsys):
    process_application(
        registrations, make_event_record(), "Мария К.", "19", "средний",
        "да", TODAY,
    )

    output = capsys.readouterr().out

    assert "Код участия" in output
    assert "заявка подтверждена" in output


def test_process_application_waiting_list(registrations):
    event = make_event_record()
    event["capacity"] = 1
    create_registration(
        registrations, DEMO_EVENT_ID, "Другой", 19, "средний", True,
        STATUS_CONFIRMED,
    )

    result = process_application(
        registrations, event, "Ольга П.", "19", "средний", "да", TODAY,
    )

    assert result == RESULT_WAITING
    assert len(registrations) == 2
    assert registrations[-1]["status"] == STATUS_PENDING


def test_process_application_rejects_without_saving(registrations):
    result = process_application(
        registrations, make_event_record(), "Артём С.", "14", "средний",
        "да", TODAY,
    )

    assert result == RESULT_REJECTED
    assert registrations == []


def test_process_application_rejects_invalid_age(registrations, capsys):
    result = process_application(
        registrations, make_event_record(), "Мария К.", "abc", "средний",
        "да", TODAY,
    )

    output = capsys.readouterr().out

    assert result == RESULT_REJECTED
    assert "целым числом" in output
    assert registrations == []


def test_process_application_rejects_finished_event(registrations):
    event = make_event_record()
    event["event_date"] = datetime.date(2026, 9, 1)

    result = process_application(
        registrations, event, "Мария К.", "19", "средний", "да", TODAY,
    )

    assert result == RESULT_REJECTED


def test_print_event_card_contains_data(club, topic, event, registrations,
                                        capsys):
    print_event_card(DEMO_EVENT_ID, event, club, topic, registrations, TODAY)

    output = capsys.readouterr().out

    assert "Философский клуб" in output
    assert "Тема дискуссии" in output
    assert "свободно 25" in output


def test_print_event_card_reports_missing_event(capsys):
    print_event_card(999, {}, {}, {}, [], TODAY)

    assert "не найдено" in capsys.readouterr().out


def test_show_functions_do_not_fail_with_empty_data(capsys):
    show_clubs({}, {})
    show_topics({})
    show_registrations([], {})
    show_statistics({}, {}, [], {})
    output = capsys.readouterr().out

    assert "Регистраций пока нет." in output


def test_show_upcoming_events_lists_planned(club, topic, event, registrations,
                                            capsys):
    event[1]["event_date"] = datetime.date(2026, 10, 15)

    show_upcoming_events(event, club, topic, registrations)

    output = capsys.readouterr().out

    assert "Философский клуб" in output


def test_show_upcoming_events_without_events(capsys):
    show_upcoming_events({}, {}, {}, {})

    assert "Предстоящих мероприятий нет." in capsys.readouterr().out


def test_input_event_id_returns_identifier(event, answers):
    answers(["1"])

    assert input_event_id(event) == 1


def test_input_event_id_skips_unknown(event, answers):
    answers(["42", "1"])

    assert input_event_id(event) == 1


def test_input_event_id_returns_none_on_cancel(event, answers):
    answers(["0"])

    assert input_event_id(event) is None


def test_check_availability_reports_free_places(event, registrations,
                                                answers, capsys):
    answers(["1"])

    check_availability(event, registrations)

    output = capsys.readouterr().out

    assert "свободно 25" in output
    assert "Мероприятие доступно" in output


def test_find_and_show_club_uses_answer(club, answers, capsys):
    answers(["философ"])

    find_and_show_club(club)

    output = capsys.readouterr().out

    assert "Найдено клубов: 1" in output


def test_find_and_show_club_without_result(club, answers, capsys):
    answers(["несуществующий"])

    find_and_show_club(club)

    assert "не найдены" in capsys.readouterr().out


def test_find_and_show_topic_uses_answer(topics, answers, capsys):
    add_topic(topics, "Первая тема", "средний", ["этика"], "Материалы")
    add_topic(topics, "Вторая тема", "средний", ["ЭТИКА"], "Материалы")
    answers(["этика"])

    find_and_show_topic(topics)

    output = capsys.readouterr().out

    assert "Найдено тем: 2" in output


def test_find_and_show_topic_without_result(topics, answers, capsys):
    answers(["нет такого тега"])

    find_and_show_topic(topics)

    assert "не найдены" in capsys.readouterr().out


def test_register_participant_adds_record(event, club, topic, registrations,
                                          answers):
    answers(["1", "Мария К.", "19", "средний", "да"])

    assert register_participant(event, club, topic, registrations) is True
    assert len(registrations) == 1


def test_register_participant_returns_false_when_cancelled(event, club, topic,
                                                           registrations,
                                                           answers):
    answers(["0"])

    assert register_participant(event, club, topic, registrations) is False
    assert registrations == []


def test_cancel_registration_by_name(registrations, answers, capsys):
    record = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True,
        STATUS_CONFIRMED,
    )
    answers(["мария", str(record["id"])])

    assert cancel_registration_by_name(registrations) is True
    assert registrations[0]["status"] != STATUS_CONFIRMED


def test_cancel_registration_by_name_without_records(registrations, answers,
                                                     capsys):
    answers(["никто"])

    assert cancel_registration_by_name(registrations) is False
    assert "не найдено" in capsys.readouterr().out


def test_confirm_registration_by_id(registrations, answers):
    record = create_registration(registrations, 1, "Мария К.", 19, "средний",
                                 True)
    answers([str(record["id"])])

    assert confirm_registration_by_id(registrations) is True
    assert registrations[0]["status"] == STATUS_CONFIRMED


def test_confirm_registration_by_id_rejects_confirmed(registrations, answers):
    record = create_registration(
        registrations, 1, "Мария К.", 19, "средний", True, STATUS_CONFIRMED
    )
    answers([str(record["id"])])

    assert confirm_registration_by_id(registrations) is False


def test_add_club_from_input(clubs, answers):
    answers(["Новый клуб", "Описание", "Модератор"])

    add_club_from_input(clubs)

    assert len(clubs) == 1
    assert clubs[1]["name"] == "Новый клуб"


def test_add_topic_from_input(topics, answers):
    answers(["Новая тема", "средний", "этика, логика", "Материалы"])

    add_topic_from_input(topics)

    assert topics[1]["tags"] == ["этика", "логика"]


def test_add_event_from_input(events, club, topic, answers):
    answers(["1", "1", "15.10.2026", "18:30", "онлайн", "ссылка", "30",
             "16", "средний"])

    add_event_from_input(events, club, topic)

    assert events[1]["capacity"] == 30
    assert events[1]["event_date"] == datetime.date(2026, 10, 15)
    assert events[1]["club_id"] == 1


def test_add_event_from_input_without_clubs(events, topic, answers, capsys):
    add_event_from_input(events, {}, topic)

    assert "Сначала добавьте" in capsys.readouterr().out
    assert events == {}


def test_add_event_from_input_without_topics(events, club, answers, capsys):
    add_event_from_input(events, club, {})

    assert "Сначала добавьте" in capsys.readouterr().out
    assert events == {}


def test_add_event_from_input_checks_unknown_club(events, club, topic,
                                                  answers, capsys):
    answers(["42"])

    add_event_from_input(events, club, topic)

    assert "не найден" in capsys.readouterr().out
    assert events == {}


def test_add_event_from_input_checks_capacity(events, club, topic, answers,
                                              capsys):
    answers(["1", "1", "15.10.2026", "18:30", "онлайн", "ссылка", "0",
             "16", "средний"])

    add_event_from_input(events, club, topic)

    assert "положительным" in capsys.readouterr().out
    assert events == {}


def test_run_menu_reads_only_options(data_dir, answers, capsys):
    seed_project()

    answers(["1", "4", "9", "10", "0"])

    run_menu()

    output = capsys.readouterr().out

    assert "Работа завершена." in output
    assert "Данные сохранены" not in output


def test_run_menu_saves_changes(data_dir, answers):
    seed_project()

    answers(["11", "Новый клуб", "Описание", "Модератор", "0"])

    run_menu()

    assert storage.load_clubs()[2]["name"] == "Новый клуб"


def test_run_menu_reports_unknown_option(data_dir, answers, capsys):
    seed_project()

    answers(["42", "0"])

    run_menu()

    assert "Нет такого пункта меню." in capsys.readouterr().out


def test_run_demo_repeats_scenario(data_dir, capsys):
    seed_project()

    run_demo()

    output = capsys.readouterr().out

    assert "подтверждено участников — 24 из 25" in output
    assert len(storage.load_registrations()) == 25


def test_run_demo_reports_missing_event(data_dir, capsys):
    seed_project(with_registrations=False, with_event=False)

    run_demo()

    assert "отсутствует в базе данных" in capsys.readouterr().out


def test_run_introspection_prints_functions(capsys):
    run_introspection()

    output = capsys.readouterr().out

    assert "Интроспекция модулей проекта" in output
    assert "get_registration_result" in output
    assert "load_project" in output


def test_run_mode_dispatches_by_number(monkeypatch):
    calls = []
    for name in ("run_demo", "run_interactive", "run_menu",
                 "run_introspection"):
        monkeypatch.setattr(
            main, name, lambda name=name: calls.append(name)
        )

    run_mode("1")
    run_mode("2")
    run_mode("3")
    run_mode("4")
    run_mode("")

    assert calls == ["run_demo", "run_interactive", "run_menu",
                     "run_introspection", "run_demo"]


def test_main_handles_end_of_input(monkeypatch, capsys):
    def raise_eof(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)

    main_entry()

    assert "Работа прервана пользователем." in capsys.readouterr().out


def test_main_starts_selected_mode(monkeypatch):
    calls = []
    answers = iter(["3"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(
        main, "run_menu", lambda: calls.append("run_menu")
    )

    main_entry()

    assert calls == ["run_menu"]


def test_project_modules_are_real_modules():
    assert main.PROJECT_MODULES == (
        clubs, topics, events, registrations, analytics, storage
    )


def test_menu_items_end_with_exit():
    assert main.MENU_ITEMS[-1] == "0. Выход"


def seed_project(with_registrations=True, with_event=True):
    """Записать начальные данные проекта во временный каталог."""
    clubs_data: dict[int, dict] = {}
    topics_data: dict[int, dict] = {}
    events_data: dict[int, dict] = {}
    registrations_data: list[dict] = []

    add_club(clubs_data, "Философский клуб", "Описание клуба", "Модератор")
    add_topic(topics_data, "Справедливость", "средний", ["этика"],
              "Материалы")
    if with_event:
        add_event(
            events_data, 1, 1, datetime.date(2026, 10, 15), "18:30",
            "онлайн", "ссылка на комнату", 25, 16, "средний",
        )
    if with_registrations:
        for number in range(23):
            create_registration(
                registrations_data, DEMO_EVENT_ID, f"Участник {number}", 19,
                "средний", True, STATUS_CONFIRMED,
            )

    storage.init_project(
        clubs_data, topics_data, events_data, registrations_data
    )


@pytest.mark.parametrize("module", [analytics, clubs, events, main,
                                    registrations, storage, topics])
def test_modules_have_docstrings(module):
    assert module.__doc__
