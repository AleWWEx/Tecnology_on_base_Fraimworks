"""Система организации дискуссионных клубов.

Приложение развивает начальный сценарий ПР1 «Запись участника на
мероприятие дискуссионного клуба»: сначала средствами коллекций и
функций (ПР2), затем объектной моделью (ПР3).

На ПР3 предметная область представлена классами пакета models:
Club, Topic, Event и Registration. Коллекции проекта — это списки
объектов List[Club], List[Topic], List[Event] и List[Registration],
связи между которыми восстанавливаются при загрузке данных.

Модуль не хранит данные в словарях и не дублирует логику модулей:
объекты создают add_club, add_topic, add_event и create_registration,
а коллекции обрабатывают функции clubs.py, topics.py, events.py,
registrations.py и analytics.py.

Программа поддерживает четыре режима работы: автоматическую
демонстрацию сценария ПР1, диалоговую регистрацию участника, меню
приложения и интроспекцию модулей и классов проекта.
"""

import datetime
import inspect
from typing import Any, List, Optional

import analytics
import clubs
import events
import registrations
import storage
import topics
from analytics import (
    count_topics_by_level,
    describe_entities,
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
    sort_clubs_by_size,
    sort_clubs_by_name,
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
    sort_events_by_date,
)
from models import Club, Event, Registration, Topic
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

PROJECT_MODELS = (Club, Topic, Event, Registration)

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
    "11. Показать объекты и их методы",
    "12. Добавить клуб",
    "13. Добавить тему дискуссии",
    "14. Добавить мероприятие",
    "0. Выход",
)

# Заявки, обрабатываемые в автоматической демонстрации (сценарий ПР1).
DEMO_APPLICATIONS = (
    ("Мария К.", "19", "средний", "да"),
    ("Ольга П.", "17", "средний", "да"),
    ("Артём С.", "14", "средний", "да"),
    ("Никита Р.", "22", "начинающий", "нет"),
)


def print_header() -> None:
    """Напечатать заголовок приложения."""
    print("=" * 62)
    print(APP_TITLE)
    print("=" * 62)


def print_menu() -> None:
    """Напечатать пункты меню приложения."""
    print()
    for item in MENU_ITEMS:
        print(item)


def print_event_card(event_id: int, events_data: List[Event],
                     clubs_data: List[Club], topics_data: List[Topic],
                     registrations_data: List[Registration],
                     today: Optional[datetime.date] = None) -> None:
    """Напечатать карточку мероприятия с учётом его данных.

    Карточка собирается методом объекта Event.render(): данные клуба и
    темы берутся из связанных объектов, а число участников считает
    модуль events.py.
    """
    event = get_event(events_data, event_id)
    if event is None:
        print(f"Мероприятие с идентификатором {event_id} не найдено.")
        return
    club = get_club(clubs_data, event.club_id)
    topic = get_topic(topics_data, event.topic_id)
    signed_up = count_active_registrations(registrations_data, event_id)
    print(get_event_card(event, club, topic, signed_up,
                         event.status_on(today)))


def process_application(registrations_data: List[Registration],
                        event: Event, name: str, age_text: str, level: str,
                        read_text: str,
                        today: Optional[datetime.date] = None) -> str:
    """Обработать заявку участника и напечатать решение.

    Параметры age_text и read_text передаются строками — так данные
    приходят из формы ввода. Возвращает результат обработки заявки:
    подтверждена, лист ожидания или отказано.

    Подтверждённая заявка и заявка листа ожидания сохраняются в
    коллекции registrations_data; отказ не сохраняется, повторная
    попытка возможна.
    """
    try:
        age = int(age_text)
    except (TypeError, ValueError):
        print("Ошибка ввода: возраст должен быть целым числом.")
        return RESULT_REJECTED

    has_read_materials = read_text.lower() == "да"
    signed_up = count_active_registrations(registrations_data, event.id)
    free_places = event.free_places(signed_up)

    result, reason = get_registration_result(
        age, level, has_read_materials, event.status_on(today), free_places,
        event.min_age, event.required_level,
    )

    print()
    print(f"--- Заявка участника {name} ---")
    print(f"Возраст: {age}, уровень: «{level}», материалы: {read_text}")
    print(f"Свободных мест: {free_places}")

    if result == RESULT_APPROVED:
        registration = create_registration(
            registrations_data, event.id, name, age, level,
            has_read_materials, STATUS_CONFIRMED,
        )
        registration.link(event)
        print(f"Решение: заявка подтверждена, {reason}.")
        print(f"Код участия: {registration.ticket_code}")
        return result

    if result == RESULT_WAITING:
        registration = create_registration(
            registrations_data, event.id, name, age, level,
            has_read_materials, STATUS_PENDING,
        )
        registration.link(event)
        print(f"Решение: лист ожидания. Причина: {reason}.")
        return result

    print(f"Решение: отказано. Причина: {reason}.")
    return result


def show_clubs(clubs_data: List[Club], events_data: List[Event]) -> None:
    """Вывести список клубов с числом их мероприятий."""
    counts = get_club_event_counts(events_data)
    print()
    print(f"{'ID':>3} {'Клуб':<36} {'Модератор':<16} {'Мероприятий':>10}")
    for club in sort_clubs_by_name(clubs_data):
        print(
            f"{club.id:>3} {club.name:<36} "
            f"{club.moderator:<16} {counts.get(club.id, 0):>10}"
        )


def show_topics(topics_data: List[Topic]) -> None:
    """Вывести список тем дискуссий, сгруппированных по сложности."""
    for level in LEVELS:
        level_topics = list(filter_topics_by_level(topics_data, level))
        print()
        print(f"Уровень «{level}»: тем — {len(level_topics)}")
        for topic in level_topics:
            tags = ", ".join(topic.tags)
            print(f"  [{topic.id}] {topic.title}")
            print(f"      теги: {tags}; материалы: {topic.materials}")


def show_registrations(registrations_data: List[Registration]) -> None:
    """Вывести регистрации участников с указанием мероприятия."""
    if not registrations_data:
        print("Регистраций пока нет.")
        return
    for registration in registrations_data:
        print()
        print(f"[{registration.id}] {registration.event_date_text()}")
        print(f"    Участник: {registration.name}")
        print(f"    Статус: {registration.status}")
        print(f"    Код участия: {registration.ticket_code}")


def show_upcoming_events(events_data: List[Event], clubs_data: List[Club],
                         topics_data: List[Topic],
                         registrations_data: List[Registration]) -> None:
    """Вывести карточки мероприятий, которые ещё не завершились."""
    upcoming = list(
        events.iter_upcoming_events(events_data, datetime.date.today())
    )
    if not upcoming:
        print("Предстоящих мероприятий нет.")
        return
    for event in upcoming:
        print()
        print_event_card(
            event.id, events_data, clubs_data, topics_data,
            registrations_data,
        )


def show_statistics(events_data: List[Event], clubs_data: List[Club],
                    registrations_data: List[Registration],
                    topics_data: List[Topic]) -> None:
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
    for club in sort_clubs_by_size(clubs_data, counts):
        print(f"  {club.name} — {counts.get(club.id, 0)}")

    print()
    print("Самые активные участники:")
    for name, count in get_top_participants(registrations_data):
        print(f"  {name} — регистраций: {count}")


def show_objects(events_data: List[Event], topics_data: List[Topic],
                 registrations_data: List[Registration]) -> None:
    """Показать полиморфное поведение объектов разных классов.

    Одинаковая операция — печать строкового представления — даёт
    разный результат для Club, Topic, Event и Registration: это и есть
    полиморфизм.
    """
    objects: List[Any] = []
    if events_data:
        objects.append(events_data[0])
    if topics_data:
        objects.append(topics_data[0])
    if registrations_data:
        objects.append(registrations_data[0])

    print("Строковое представление объектов:")
    for line in describe_entities(objects):
        print(f"  {line}")

    first_event = get_event(events_data, DEMO_EVENT_ID)
    if first_event is not None and first_event.topic is not None:
        print()
        print("Данные связанных объектов доступны через мероприятие:")
        print(f"  тема: {first_event.topic.title}")
        print(f"  уровень темы: {first_event.topic.level}")
        print(f"  клуб: {first_event.club_name()}")


def find_and_show_club(clubs_data: List[Club]) -> None:
    """Найти клуб по названию и вывести его карточку."""
    query = input_text("Подстрока названия или описания: ")
    found = find_club(clubs_data, query)
    if not found:
        print(f"По запросу «{query}» клубы не найдены.")
        return
    print(f"Найдено клубов: {len(found)}")
    counts = {club.id: 0 for club in found}
    for club in found:
        print()
        print(get_club_card(club))
    print()
    print(f"Идентификаторы найденных клубов: {list(counts)}")


def find_and_show_topic(topics_data: List[Topic]) -> None:
    """Найти темы по тегу и вывести их карточки."""
    tag = input_text("Тег: ")
    found = find_topics_by_tag(topics_data, tag)
    if not found:
        print(f"По тегу «{tag}» темы не найдены.")
        return
    print(f"Найдено тем: {len(found)}")
    for topic in found:
        print()
        print(f"[{topic.id}]")
        print(f"    {topic.title}")


def check_availability(events_data: List[Event],
                       registrations_data: List[Registration]) -> None:
    """Проверить доступность выбранного мероприятия."""
    event_id = input_event_id(events_data)
    if event_id is None:
        return
    event = get_event(events_data, event_id)
    if event is None:
        return
    signed_up = count_active_registrations(registrations_data, event_id)
    status = event.status_on()
    print(f"Дата мероприятия: {format_date(event.event_date)} "
          f"({status})")
    print(f"Мест: {signed_up} из {event.capacity}, "
          f"свободно {event.free_places(signed_up)}")
    is_available = is_event_available(
        events_data, registrations_data, event_id
    )
    print(get_availability_text(is_available))


def register_participant(events_data: List[Event], clubs_data: List[Club],
                         topics_data: List[Topic],
                         registrations_data: List[Registration]) -> bool:
    """Записать участника на мероприятие.

    Возвращает True, если в коллекцию добавлен новый объект
    Registration.
    """
    event_id = input_event_id(events_data)
    if event_id is None:
        return False
    event = get_event(events_data, event_id)
    if event is None:
        return False
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


def cancel_registration_by_name(
        registrations_data: List[Registration]) -> bool:
    """Отменить регистрацию участника, найденную по имени.

    Возвращает True, если объект заявки был отменён.
    """
    name = input_text("Имя участника: ")
    found = find_registrations_by_name(registrations_data, name)
    active = [
        registration for registration in found
        if registration.status != STATUS_CANCELLED
    ]
    if not active:
        print(f"Активных регистраций по имени «{name}» не найдено.")
        return False
    for registration in active:
        print(
            f"  [{registration.id}] мероприятие "
            f"{registration.event_id}, "
            f"статус «{registration.status}»"
        )
    registration_id = input_int("Идентификатор отменяемой записи: ")
    if not cancel_registration(registrations_data, registration_id):
        print(f"Запись с идентификатором {registration_id} не найдена.")
        return False
    print(f"Регистрация {registration_id} отменена: "
          "освободившееся место снова доступно.")
    return True


def confirm_registration_by_id(
        registrations_data: List[Registration]) -> bool:
    """Подтвердить заявку, ожидающую подтверждения.

    Возвращает True, если состояние объекта заявки изменилось.
    """
    registration_id = input_int("Идентификатор заявки: ")
    if not confirm_registration(registrations_data, registration_id):
        print(f"Заявку {registration_id} нельзя подтвердить.")
        return False
    print(f"Заявка {registration_id} подтверждена.")
    return True


def input_event_id(events_data: List[Event]) -> Optional[int]:
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


def add_club_from_input(clubs_data: List[Club]) -> Club:
    """Добавить новый клуб, заданный пользователем.

    Возвращает созданный объект Club.
    """
    name = input_text("Название клуба: ")
    description = input_text("Описание: ")
    moderator = input_text("Модератор: ")
    club = add_club(clubs_data, name, description, moderator)
    print(f"Клуб добавлен под идентификатором {club.id}.")
    return club


def add_topic_from_input(topics_data: List[Topic]) -> Topic:
    """Добавить новую тему дискуссии, заданную пользователем.

    Возвращает созданный объект Topic.
    """
    title = input_text("Название темы: ")
    level = input_choice("Уровень сложности", LEVELS)
    tags_text = input_text("Теги через запятую: ")
    materials = input_text("Рекомендованные материалы: ")
    tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
    topic = add_topic(topics_data, title, level, tags, materials)
    print(f"Тема добавлена под идентификатором {topic.id}.")
    return topic


def add_event_from_input(events_data: List[Event], clubs_data: List[Club],
                         topics_data: List[Topic]) -> Optional[Event]:
    """Добавить новое мероприятие, заданное пользователем.

    Идентификаторы клуба и темы проверяются: объект с несуществующими
    связями создавать нельзя. Возвращает созданный объект Event или
    None, если данные неполны.
    """
    if not clubs_data:
        print("Сначала добавьте хотя бы один клуб.")
        return None
    if not topics_data:
        print("Сначала добавьте хотя бы одну тему.")
        return None
    club_id = input_int("Идентификатор клуба: ")
    club = get_club(clubs_data, club_id)
    if club is None:
        print(f"Клуб с идентификатором {club_id} не найден.")
        return None
    topic_id = input_int("Идентификатор темы: ")
    topic = get_topic(topics_data, topic_id)
    if topic is None:
        print(f"Тема с идентификатором {topic_id} не найдена.")
        return None
    event_date = input_date("Дата проведения (ДД.ММ.ГГГГ): ")
    start_time = input_text("Время начала (ЧЧ:ММ): ")
    event_format = input_choice("Формат", EVENT_FORMATS)
    place = input_text("Место или ссылка: ")
    capacity = input_int("Вместимость: ")
    if capacity <= 0:
        print("Вместимость должна быть положительным числом.")
        return None
    min_age = input_int("Минимальный возраст: ")
    required_level = input_choice("Требуемый уровень", LEVELS)
    event = add_event(
        events_data, club.id, topic.id, event_date, start_time,
        event_format, place, capacity, min_age, required_level,
    )
    event.link(club=club, topic=topic)
    print(f"Мероприятие добавлено под идентификатором {event.id}.")
    return event


def run_menu() -> None:
    """Интерактивное меню приложения.

    Данные загружаются при запуске как объекты и сохраняются в файлы
    при выходе, если пользователь внёс изменения.
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
            show_registrations(registrations_data)
        elif choice == 10:
            show_statistics(
                events_data, clubs_data, registrations_data, topics_data
            )
        elif choice == 11:
            show_objects(events_data, topics_data, registrations_data)
        elif choice == 12:
            add_club_from_input(clubs_data)
            changed = True
        elif choice == 13:
            add_topic_from_input(topics_data)
            changed = True
        elif choice == 14:
            add_event_from_input(events_data, clubs_data, topics_data)
            changed = True
        else:
            print("Нет такого пункта меню.")

    if changed:
        save_project(clubs_data, topics_data, events_data, registrations_data)
        print("\nДанные сохранены в каталог data.")
    print("Работа завершена.")


def run_demo() -> None:
    """Автоматическая демонстрация: четыре заявки участников.

    Сценарий ПР1: заявки обрабатываются последовательно, подтверждённые
    заявки увеличивают число занятых мест и влияют на следующие решения.
    Результат сохраняется в каталог data.
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

    print()
    print(f"Итог: подтверждено участников — {confirmed} "
          f"из {event.capacity}.")
    print(f"Всего заявок в базе: {len(registrations_data)}.")
    save_project(clubs_data, topics_data, events_data, registrations_data)
    print("Данные сохранены в каталог data.")
    print("Все заявки обработаны.")


def run_interactive() -> None:
    """Диалоговый режим: данные заявки вводит пользователь.

    Сценарий ПР1. Пользователь выбирает мероприятие и вводит данные
    заявки; некорректный ввод обрабатывается без прерывания программы.
    """
    print_header()

    clubs_data, topics_data, events_data, registrations_data = load_project()
    print("Выберите мероприятие:")
    for event in sort_events_by_date(events_data):
        print(
            f"  {event.id}. {format_date(event.event_date)} "
            f"{event.start_time}, {event.format}"
        )

    event_id = input_event_id(events_data)
    if event_id is None:
        print("Регистрация отменена пользователем.")
        return
    event = get_event(events_data, event_id)
    if event is None:
        return

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


def run_introspection() -> None:
    """Показать функции модулей и методы классов проекта.

    Используется интроспекция: модуль inspect во время выполнения
    программы позволяет получить состав модуля, сигнатуры функций,
    методы классов и тексты их документации без обращения к исходному
    коду.
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

    print()
    print("Интроспекция классов предметной области")
    print("-" * 60)
    for model in PROJECT_MODELS:
        print(f"Класс {model.__name__}")
        print(f"  базовый класс: {model.__bases__[0].__name__}")
        print(f"  описание: {inspect.getdoc(model).splitlines()[0]}")
        for name, member in inspect.getmembers(model, inspect.isfunction):
            if name.startswith("__") and name not in ("__init__", "__str__"):
                continue
            print(f"  {name}{inspect.signature(member)}")
        print()


def main() -> None:
    """Точка входа: выбор режима работы программы.

    Прерывание работы пользователем и исчерпание ввода перехватываются:
    программа завершается с сообщением, а не с трассировкой ошибки.
    """
    print("Выберите режим работы:")
    print("  1 — автоматическая демонстрация сценария")
    print("  2 — интерактивная регистрация участника")
    print("  3 — меню приложения")
    print("  4 — интроспекция модулей и классов проекта")

    try:
        mode = input("Номер режима (по умолчанию 1): ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nРабота прервана пользователем.")
        return
    run_mode(mode)


def run_mode(mode: str) -> None:
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
