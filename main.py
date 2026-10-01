"""Система организации дискуссионных клубов.

Приложение развивает начальный сценарий ПР1 «Запись участника на
мероприятие дискуссионного клуба» средствами, изученными на ПР2:
коллекциями, функциями, циклами, модулями, файлами и обработкой
исключений.

Сценарий ПР1 сохранён и переработан: решение по заявке принимает функция
get_registration_result() модуля registrations.py, а данные приходят из
коллекций проекта, загруженных из JSON-файлов каталога data.

Программа поддерживает четыре режима работы: автоматическую
демонстрацию сценария ПР1, диалоговую регистрацию участника, меню
приложения и интроспекцию модулей проекта.
"""

import datetime
import inspect

import analytics
import clubs
import events
import registrations
import storage
import topics
from analytics import (
    count_topics_by_level,
    format_event_statistics,
    format_topics_by_level,
    get_club_event_counts,
    get_event_statistics,
    get_top_participants,
)
from clubs import (
    add_club,
    find_club,
    get_club,
    get_club_card,
    sort_club_ids_by_name,
    sort_club_ids_by_size,
)
from events import (
    EVENT_FORMATS,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
    STATUS_PENDING,
    add_event,
    count_active_registrations,
    get_event,
    get_event_card,
    get_event_status,
    get_free_places,
    iter_upcoming_events,
    sort_events_by_date,
)
from registrations import (
    RESULT_APPROVED,
    RESULT_REJECTED,
    RESULT_WAITING,
    cancel_registration,
    confirm_registration,
    create_registration,
    find_registrations_by_name,
    get_availability_text,
    get_registration_result,
    is_event_available,
)
from storage import load_project, save_project
from topics import (
    LEVELS,
    add_topic,
    filter_topics_by_level,
    find_topics_by_tag,
    get_topic,
)
from utils import format_date, input_choice, input_date, input_int, input_text

APP_TITLE = "СИСТЕМА ОРГАНИЗАЦИИ ДИСКУССИОННЫХ КЛУБОВ"

# Опорная дата автономной демонстрации: вывод сценария воспроизводим.
DEMO_TODAY = datetime.date(2026, 10, 1)
DEMO_EVENT_ID = 1

PROJECT_MODULES = (clubs, topics, events, registrations, analytics, storage)

MENU_ITEMS = (
    "1. Показать клубы",
    "2. Найти клуб по названию",
    "3. Найти темы по тегу и уровню",
    "4. Показать ближайшие мероприятия",
    "5. Проверить доступность мероприятия",
    "6. Записаться на мероприятие",
    "7. Подтвердить заявку из листа ожидания",
    "8. Отменить регистрацию",
    "9. Показать регистрации",
    "10. Показать статистику",
    "11. Добавить клуб",
    "12. Добавить тему дискуссии",
    "13. Добавить мероприятие",
    "0. Выход",
)

# Заявки, обрабатываемые в автоматической демонстрации (сценарий ПР1).
DEMO_APPLICATIONS = (
    ("Мария К.", "19", "средний", "да"),
    ("Ольга П.", "17", "средний", "да"),
    ("Артём С.", "14", "средний", "да"),
    ("Никита Р.", "22", "начинающий", "нет"),
)


def print_header():
    """Напечатать заголовок приложения."""
    print("=" * 62)
    print(APP_TITLE)
    print("=" * 62)


def print_menu():
    """Напечатать пункты меню приложения."""
    print()
    for item in MENU_ITEMS:
        print(item)


def print_event_card(event_id, events_data, clubs_data, topics_data,
                     registrations_data, today=None):
    """Напечатать карточку мероприятия с учётом его данных.

    Карточка собирается функцией get_event_card из событийной части
    проекта; остальные модули предоставляют данные клуба, темы и число
    участников.
    """
    event = get_event(events_data, event_id)
    if event is None:
        print(f"Мероприятие с идентификатором {event_id} не найдено.")
        return
    club = get_club(clubs_data, event["club_id"])
    topic = get_topic(topics_data, event["topic_id"])
    signed_up = count_active_registrations(registrations_data, event_id)
    status = get_event_status(event["event_date"], today)
    print(get_event_card(event, club, topic, signed_up, status))


def process_application(registrations, event, name, age_text, level,
                        read_text, today=None):
    """Обработать заявку участника и напечатать решение.

    Параметры age_text и read_text передаются строками — так данные
    приходят из формы ввода. Возвращает результат обработки заявки:
    подтверждена, лист ожидания или отказано.

    Подтверждённая заявка и заявка листа ожидания сохраняются в списке
    registrations; отказ не сохраняется, повторная попытка возможна.
    """
    try:
        age = int(age_text)
    except (TypeError, ValueError):
        print("Ошибка ввода: возраст должен быть целым числом.")
        return RESULT_REJECTED

    has_read_materials = read_text.lower() == "да"
    event_id = int(event["id"])
    signed_up = count_active_registrations(registrations, event_id)
    free_places = get_free_places(signed_up, int(event["capacity"]))
    status = get_event_status(event["event_date"], today)

    result, reason = get_registration_result(
        age, level, has_read_materials, status, free_places,
        int(event["min_age"]), str(event["required_level"]),
    )

    print()
    print(f"--- Заявка участника {name} ---")
    print(f"Возраст: {age}, уровень: «{level}», материалы: {read_text}")
    print(f"Свободных мест: {free_places}")

    if result == RESULT_APPROVED:
        record = create_registration(
            registrations, event_id, name, age, level,
            has_read_materials, STATUS_CONFIRMED,
        )
        print(f"Решение: заявка подтверждена, {reason}.")
        print(f"Код участия: {record['ticket_code']}")
        return result

    if result == RESULT_WAITING:
        create_registration(
            registrations, event_id, name, age, level,
            has_read_materials, STATUS_PENDING,
        )
        print(f"Решение: лист ожидания. Причина: {reason}.")
        return result

    print(f"Решение: отказано. Причина: {reason}.")
    return result


def show_clubs(clubs_data, events_data):
    """Вывести список клубов с числом их мероприятий."""
    counts = get_club_event_counts(events_data)
    print()
    print(f"{'ID':>3} {'Клуб':<36} {'Модератор':<16} {'Мероприятий':>10}")
    for club_id in sort_club_ids_by_name(clubs_data):
        club = clubs_data[club_id]
        print(
            f"{club_id:>3} {club['name']:<36} "
            f"{club['moderator']:<16} {counts.get(club_id, 0):>10}"
        )


def show_topics(topics_data):
    """Вывести список тем дискуссий, сгруппированных по сложности."""
    for level in LEVELS:
        level_topics = list(filter_topics_by_level(topics_data, level))
        print()
        print(f"Уровень «{level}»: тем — {len(level_topics)}")
        for topic_id in level_topics:
            topic = topics_data[topic_id]
            tags = ", ".join(topic["tags"])
            print(f"  [{topic_id}] {topic['title']}")
            print(f"      теги: {tags}; материалы: {topic['materials']}")


def show_registrations(registrations_data, events_data):
    """Вывести регистрации участников с указанием мероприятия."""
    if not registrations_data:
        print("Регистраций пока нет.")
        return
    for record in registrations_data:
        event = get_event(events_data, record["event_id"])
        event_date = "мероприятие не найдено"
        if event is not None:
            event_date = format_date(event["event_date"])
        print()
        print(f"[{record['id']}] {event_date}")
        print(f"    Участник: {record['name']}")
        print(f"    Статус: {record['status']}")
        print(f"    Код участия: {record['ticket_code']}")


def show_upcoming_events(events_data, clubs_data, topics_data,
                         registrations_data):
    """Вывести карточки мероприятий, которые ещё не завершились."""
    upcoming = list(iter_upcoming_events(events_data, datetime.date.today()))
    if not upcoming:
        print("Предстоящих мероприятий нет.")
        return
    for event_id in upcoming:
        print()
        print_event_card(
            event_id, events_data, clubs_data, topics_data,
            registrations_data,
        )


def show_statistics(events_data, clubs_data, registrations_data,
                    topics_data):
    """Вывести сводную статистику по мероприятиям и участникам."""
    summary = get_event_statistics(events_data, registrations_data)
    print()
    print(format_event_statistics(
        "Заполненность мероприятий", events_data, summary
    ))
    print()
    print(format_topics_by_level(count_topics_by_level(topics_data)))

    counts = get_club_event_counts(events_data)
    print()
    print("Клубы по числу мероприятий:")
    for club_id in sort_club_ids_by_size(clubs_data, counts):
        print(f"  {clubs_data[club_id]['name']} — "
              f"{counts.get(club_id, 0)}")

    print()
    print("Самые активные участники:")
    for name, count in get_top_participants(registrations_data):
        print(f"  {name} — регистраций: {count}")


def find_and_show_club(clubs_data):
    """Найти клуб по названию и вывести его карточку."""
    query = input_text("Подстрока названия или описания: ")
    found = find_club(clubs_data, query)
    if not found:
        print(f"По запросу «{query}» клубы не найдены.")
        return
    print(f"Найдено клубов: {len(found)}")
    for club_id in found:
        print()
        print(get_club_card(clubs_data[club_id]))


def find_and_show_topic(topics_data):
    """Найти темы по тегу и вывести их карточки."""
    tag = input_text("Тег: ")
    found = find_topics_by_tag(topics_data, tag)
    if not found:
        print(f"По тегу «{tag}» темы не найдены.")
        return
    print(f"Найдено тем: {len(found)}")
    for topic_id in found:
        print()
        print(f"[{topic_id}]")
        print(f"    {topics_data[topic_id]['title']}")


def check_availability(events_data, registrations_data):
    """Проверить доступность выбранного мероприятия."""
    event_id = input_event_id(events_data)
    if event_id is None:
        return
    event = get_event(events_data, event_id)
    signed_up = count_active_registrations(registrations_data, event_id)
    free_places = get_free_places(signed_up, int(event["capacity"]))
    status = get_event_status(event["event_date"])
    print(f"Дата мероприятия: {format_date(event['event_date'])} "
          f"({status})")
    print(f"Мест: {signed_up} из {event['capacity']}, "
          f"свободно {free_places}")
    is_available = is_event_available(
        events_data, registrations_data, event_id
    )
    print(get_availability_text(is_available))


def register_participant(events_data, clubs_data, topics_data,
                         registrations_data):
    """Записать участника на мероприятие.

    Возвращает True, если в базу добавлена новая запись.
    """
    event_id = input_event_id(events_data)
    if event_id is None:
        return False
    event = get_event(events_data, event_id)
    print()
    print_event_card(
        event_id, events_data, clubs_data, topics_data, registrations_data
    )
    name = input_text("Введите имя участника: ")
    age_text = str(input_int("Введите возраст: "))
    level = input_choice("Уровень подготовки", LEVELS)
    read_text = input_choice(
        "Прочитаны рекомендованные материалы?", ("да", "нет")
    )
    size_before = len(registrations_data)
    process_application(
        registrations_data, event, name, age_text, level, read_text
    )
    return len(registrations_data) != size_before


def cancel_registration_by_name(registrations_data):
    """Отменить регистрацию участника, найденную по имени.

    Возвращает True, если запись была отменена.
    """
    name = input_text("Имя участника: ")
    found = find_registrations_by_name(registrations_data, name)
    active = [
        record for record in registrations_data
        if record["id"] in found and record["status"] != STATUS_CANCELLED
    ]
    if not active:
        print(f"Активных регистраций по имени «{name}» не найдено.")
        return False
    for record in active:
        print(
            f"  [{record['id']}] мероприятие {record['event_id']}, "
            f"статус «{record['status']}»"
        )
    registration_id = input_int("Идентификатор отменяемой записи: ")
    if not cancel_registration(registrations_data, registration_id):
        print(f"Запись с идентификатором {registration_id} не найдена.")
        return False
    print(f"Регистрация {registration_id} отменена: "
          "освободившееся место снова доступно.")
    return True


def confirm_registration_by_id(registrations_data):
    """Подтвердить заявку, ожидающую подтверждения.

    Возвращает True, если заявка была подтверждена.
    """
    registration_id = input_int("Идентификатор заявки: ")
    if not confirm_registration(registrations_data, registration_id):
        print(f"Заявку {registration_id} нельзя подтвердить.")
        return False
    print(f"Заявка {registration_id} подтверждена.")
    return True


def input_event_id(events_data):
    """Запросить идентификатор существующего мероприятия.

    Возвращает None, если пользователь отказался от выбора, введя 0.
    """
    while True:
        event_id = input_int("Идентификатор мероприятия (0 — отмена): ")
        if event_id == 0:
            return None
        if get_event(events_data, event_id) is not None:
            return event_id
        print(f"Мероприятие с идентификатором {event_id} не найдено.")


def add_club_from_input(clubs_data):
    """Добавить новый клуб, заданный пользователем."""
    name = input_text("Название клуба: ")
    description = input_text("Описание: ")
    moderator = input_text("Модератор: ")
    club_id = add_club(clubs_data, name, description, moderator)
    print(f"Клуб добавлен под идентификатором {club_id}.")


def add_topic_from_input(topics_data):
    """Добавить новую тему дискуссии, заданную пользователем."""
    title = input_text("Название темы: ")
    level = input_choice("Уровень сложности", LEVELS)
    tags_text = input_text("Теги через запятую: ")
    materials = input_text("Рекомендованные материалы: ")
    tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
    topic_id = add_topic(topics_data, title, level, tags, materials)
    print(f"Тема добавлена под идентификатором {topic_id}.")


def add_event_from_input(events_data, clubs_data, topics_data):
    """Добавить новое мероприятие, заданное пользователем.

    Идентификаторы клуба и темы проверяются: запись с несуществующими
    связями создавать нельзя.
    """
    if not clubs_data:
        print("Сначала добавьте хотя бы один клуб.")
        return
    if not topics_data:
        print("Сначала добавьте хотя бы одну тему.")
        return
    club_id = input_int("Идентификатор клуба: ")
    if get_club(clubs_data, club_id) is None:
        print(f"Клуб с идентификатором {club_id} не найден.")
        return
    topic_id = input_int("Идентификатор темы: ")
    if get_topic(topics_data, topic_id) is None:
        print(f"Тема с идентификатором {topic_id} не найдена.")
        return
    event_date = input_date("Дата проведения (ДД.ММ.ГГГГ): ")
    start_time = input_text("Время начала (ЧЧ:ММ): ")
    event_format = input_choice("Формат", EVENT_FORMATS)
    place = input_text("Место или ссылка: ")
    capacity = input_int("Вместимость: ")
    if capacity <= 0:
        print("Вместимость должна быть положительным числом.")
        return
    min_age = input_int("Минимальный возраст: ")
    required_level = input_choice("Требуемый уровень", LEVELS)
    event_id = add_event(
        events_data, club_id, topic_id, event_date, start_time,
        event_format, place, capacity, min_age, required_level,
    )
    print(f"Мероприятие добавлено под идентификатором {event_id}.")


def run_menu():
    """Интерактивное меню приложения.

    Данные загружаются при запуске и сохраняются в файлы при выходе,
    если пользователь внёс изменения.
    """
    print_header()
    clubs_data, topics_data, events_data, registrations_data = (
        load_project()
    )
    changed = False

    while True:
        print_menu()
        choice = input_int("Выберите действие: ")
        if choice == 0:
            break
        if choice == 1:
            show_clubs(clubs_data, events_data)
        elif choice == 2:
            find_and_show_club(clubs_data)
        elif choice == 3:
            find_and_show_topic(topics_data)
        elif choice == 4:
            show_upcoming_events(
                events_data, clubs_data, topics_data, registrations_data
            )
        elif choice == 5:
            check_availability(events_data, registrations_data)
        elif choice == 6:
            if register_participant(
                events_data, clubs_data, topics_data, registrations_data
            ):
                changed = True
        elif choice == 7:
            if confirm_registration_by_id(registrations_data):
                changed = True
        elif choice == 8:
            if cancel_registration_by_name(registrations_data):
                changed = True
        elif choice == 9:
            show_registrations(registrations_data, events_data)
        elif choice == 10:
            show_statistics(
                events_data, clubs_data, registrations_data, topics_data
            )
        elif choice == 11:
            add_club_from_input(clubs_data)
            changed = True
        elif choice == 12:
            add_topic_from_input(topics_data)
            changed = True
        elif choice == 13:
            add_event_from_input(events_data, clubs_data, topics_data)
            changed = True
        else:
            print("Нет такого пункта меню.")

    if changed:
        save_project(clubs_data, topics_data, events_data, registrations_data)
        print("\nДанные сохранены в каталог data.")
    print("Работа завершена.")


def run_demo():
    """Автоматическая демонстрация: четыре заявки участников.

    Сценарий ПР1: заявки обрабатываются последовательно, подтверждённые
    заявки увеличивают число занятых мест и влияют на следующие
    решения. Результат сохраняется в каталог data.
    """
    print_header()

    clubs_data, topics_data, events_data, registrations_data = load_project()
    event = get_event(events_data, DEMO_EVENT_ID)
    if event is None:
        print(f"Мероприятие {DEMO_EVENT_ID} отсутствует в базе данных.")
        return

    print()
    print_event_card(
        DEMO_EVENT_ID, events_data, clubs_data, topics_data,
        registrations_data, DEMO_TODAY,
    )

    signed_up = count_active_registrations(registrations_data, DEMO_EVENT_ID)
    confirmed = signed_up
    for name, age_text, level, read_text in DEMO_APPLICATIONS:
        result = process_application(
            registrations_data, event, name, age_text, level, read_text,
            DEMO_TODAY,
        )
        if result == RESULT_APPROVED:
            confirmed += 1

    capacity = int(event["capacity"])
    print()
    print(f"Итог: подтверждено участников — {confirmed} из {capacity}.")
    print(f"Всего заявок в базе: {len(registrations_data)}.")
    save_project(clubs_data, topics_data, events_data, registrations_data)
    print("Данные сохранены в каталог data.")
    print("Все заявки обработаны.")


def run_interactive():
    """Диалоговый режим: данные заявки вводит пользователь.

    Сценарий ПР1. Пользователь выбирает мероприятие и вводит данные
    заявки; некорректный ввод обрабатывается без прерывания программы.
    """
    print_header()

    clubs_data, topics_data, events_data, registrations_data = load_project()
    print("Выберите мероприятие:")
    for event_id in sort_events_by_date(events_data):
        event = events_data[event_id]
        print(
            f"  {event_id}. {format_date(event['event_date'])} "
            f"{event['start_time']}, {event['format']}"
        )

    event_id = input_event_id(events_data)
    if event_id is None:
        print("Регистрация отменена пользователем.")
        return
    event = get_event(events_data, event_id)

    print()
    print_event_card(
        event_id, events_data, clubs_data, topics_data, registrations_data
    )

    name = input_text("Введите имя участника: ")
    age_text = str(input_int("Введите возраст: "))
    level = input_choice("Уровень подготовки", LEVELS)
    read_text = input_choice(
        "Прочитаны рекомендованные материалы?", ("да", "нет")
    )

    process_application(
        registrations_data, event, name, age_text, level, read_text
    )
    save_project(clubs_data, topics_data, events_data, registrations_data)
    print("Данные сохранены в каталог data.")


def run_introspection():
    """Показать функции модулей проекта: имя, сигнатуру, описание.

    Используется интроспекция: модуль inspect во время выполнения
    программы позволяет получить состав модуля, сигнатуры функций и
    тексты их документации без обращения к исходному коду.
    """
    print_header()
    print("Интроспекция модулей проекта")
    for module in PROJECT_MODULES:
        print()
        print(f"Модуль {module.__name__}.py")
        print("-" * 60)
        module_functions = [
            (name, function)
            for name, function in inspect.getmembers(
                module, inspect.isfunction
            )
            if not name.startswith("_")
            and function.__module__ == module.__name__
        ]
        for name, function in module_functions:
            summary = (inspect.getdoc(function) or "").splitlines()
            description = summary[0] if summary else "нет описания"
            print(f"  {name}{inspect.signature(function)}")
            print(f"      {description}")


def main():
    """Точка входа: выбор режима работы программы.

    Прерывание работы пользователем и исчерпание ввода перехватываются:
    программа завершается с сообщением, а не с трассировкой ошибки.
    """
    print("Выберите режим работы:")
    print("  1 — автоматическая демонстрация сценария")
    print("  2 — интерактивная регистрация участника")
    print("  3 — меню приложения")
    print("  4 — интроспекция модулей проекта")

    try:
        mode = input("Номер режима (по умолчанию 1): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nРабота прервана пользователем.")
        return
    run_mode(mode)


def run_mode(mode: str):
    """Запустить выбранный режим работы программы."""
    if mode == "2":
        run_interactive()
    elif mode == "3":
        run_menu()
    elif mode == "4":
        run_introspection()
    else:
        run_demo()


if __name__ == "__main__":
    main()
