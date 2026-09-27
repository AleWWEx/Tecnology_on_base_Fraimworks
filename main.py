"""Система организации дискуссионных клубов.

Начальный сценарий ПР1: проверка возможности записи участника
на мероприятие дискуссионного клуба.
"""

import datetime
from random import randint

# --- Данные мероприятия -------------------------------------------------

CLUB_NAME = "Философский дискуссионный клуб"
EVENT_TITLE = "Дебаты: искусственный интеллект и этика"
EVENT_DATE = datetime.date(2026, 10, 15)
EVENT_START_TIME = "18:30"
EVENT_FORMAT = "онлайн"
EVENT_PLACE = "ссылка на комнату присылается после подтверждения"
MIN_AGE = 16
REQUIRED_LEVEL = "средний"
CAPACITY = 25
CURRENT_PARTICIPANTS = 23

# Опорная дата автономной демонстрации: вывод сценария воспроизводим.
DEMO_TODAY = datetime.date(2026, 10, 1)

# --- Статусы мероприятия и результаты обработки заявки ------------------

STATUS_PLANNED = "планируется"
STATUS_RUNNING = "идёт"
STATUS_FINISHED = "завершено"

RESULT_APPROVED = "подтверждена"
RESULT_WAITING = "лист ожидания"
RESULT_REJECTED = "отказано"


def get_event_status(event_date, today=None):
    """Определяет статус мероприятия по дате его проведения."""
    if today is None:
        today = datetime.date.today()
    if event_date < today:
        return STATUS_FINISHED
    if event_date == today:
        return STATUS_RUNNING
    return STATUS_PLANNED


def get_free_places(current_participants, capacity):
    """Возвращает число свободных мест, не меньше нуля."""
    free_places = capacity - current_participants
    if free_places < 0:
        return 0
    return free_places


def check_requirements(age, level, has_read_materials):
    """Проверяет требования мероприятия.

    Возвращает текст первой невыполненной причины. Если все требования
    выполнены, возвращает пустую строку.
    """
    if age < MIN_AGE:
        return f"возраст {age} лет меньше допустимых {MIN_AGE}"
    if not has_read_materials:
        return "рекомендованные материалы не прочитаны"
    if level != REQUIRED_LEVEL:
        return f"уровень «{level}» не подходит, нужен «{REQUIRED_LEVEL}»"
    return ""


def get_registration_result(age, level, has_read_materials, event_status,
                            free_places):
    """Принимает решение по заявке участника.

    Возвращает пару: результат обработки заявки и его пояснение.
    """
    if event_status == STATUS_FINISHED:
        return RESULT_REJECTED, "мероприятие уже завершено"

    reason = check_requirements(age, level, has_read_materials)
    if reason != "":
        return RESULT_REJECTED, reason

    if free_places == 0:
        return RESULT_WAITING, "свободных мест нет"

    if free_places < 3 and age < 18:
        return RESULT_WAITING, "приоритет у участников 18 лет и старше"

    return RESULT_APPROVED, "требования выполнены, места есть"


def generate_ticket_code():
    """Создаёт код участия, например DC-4821."""
    return f"DC-{randint(1000, 9999):04d}"


def get_event_card(current_participants, free_places, event_status):
    """Формирует текстовую карточку мероприятия для вывода."""
    card = (
        f"Клуб: {CLUB_NAME}\n"
        f"Тема: {EVENT_TITLE}\n"
        f"Дата: {EVENT_DATE.strftime('%d.%m.%Y')}, начало в "
        f"{EVENT_START_TIME}\n"
        f"Формат: {EVENT_FORMAT} ({EVENT_PLACE})\n"
        f"Требования: возраст {MIN_AGE}+, уровень «{REQUIRED_LEVEL}», "
        "рекомендованные материалы прочитаны\n"
        f"Места: занято {current_participants} из {CAPACITY}, "
        f"свободно {free_places}\n"
        f"Статус мероприятия: {event_status}"
    )
    return card


def process_application(name, age_text, level, read_text,
                        current_participants, event_status):
    """Обрабатывает заявку участника и печатает решение.

    Параметры name, age_text, read_text передаются строками — так данные
    приходят из формы. Возвращает новое число подтверждённых участников.
    """
    age = int(age_text)
    has_read_materials = read_text == "да"
    free_places = get_free_places(current_participants, CAPACITY)

    result, reason = get_registration_result(
        age, level, has_read_materials, event_status, free_places
    )

    print(f"\n--- Заявка участника {name} ---")
    print(f"Возраст: {age}, уровень: «{level}», материалы: {read_text}")
    print(f"Свободных мест: {free_places}")

    if result == RESULT_REJECTED:
        print(f"Решение: отказано. Причина: {reason}.")
        return current_participants

    if result == RESULT_WAITING:
        print(f"Решение: лист ожидания. Причина: {reason}.")
        return current_participants

    print(f"Решение: заявка подтверждена, {reason}.")
    print(f"Код участия: {generate_ticket_code()}")
    return current_participants + 1


def run_demo():
    """Автоматическая демонстрация: четыре заявки участников."""
    print("=" * 62)
    print("СИСТЕМА ОРГАНИЗАЦИИ ДИСКУССИОННЫХ КЛУБОВ")
    print("=" * 62)

    event_status = get_event_status(EVENT_DATE, DEMO_TODAY)
    free_places = get_free_places(CURRENT_PARTICIPANTS, CAPACITY)
    print()
    print(get_event_card(CURRENT_PARTICIPANTS, free_places, event_status))

    participants = CURRENT_PARTICIPANTS
    participants = process_application(
        "Мария К.", "19", "средний", "да", participants, event_status
    )
    participants = process_application(
        "Ольга П.", "17", "средний", "да", participants, event_status
    )
    participants = process_application(
        "Артём С.", "14", "средний", "да", participants, event_status
    )
    participants = process_application(
        "Никита Р.", "22", "начинающий", "нет", participants, event_status
    )

    print()
    print(f"Итог: подтверждено участников — {participants} из {CAPACITY}.")
    print("Все заявки обработаны.")


def run_interactive():
    """Диалоговый режим: данные заявки вводит пользователь."""
    print("=" * 62)
    print("РЕГИСТРАЦИЯ УЧАСТНИКА")
    print("=" * 62)

    event_status = get_event_status(EVENT_DATE)
    free_places = get_free_places(CURRENT_PARTICIPANTS, CAPACITY)
    print()
    print(get_event_card(CURRENT_PARTICIPANTS, free_places, event_status))

    name = input("\nВведите имя участника: ")
    age_text = input("Введите возраст: ").strip()
    if not age_text.isdigit():
        print("Ошибка ввода: возраст должен быть целым числом.")
        return

    level = input("Уровень подготовки (новичок/средний/продвинутый): ")
    read_text = input("Прочитаны рекомендованные материалы? (да/нет): ")

    process_application(
        name.strip(), age_text, level.strip(), read_text.strip(),
        CURRENT_PARTICIPANTS, event_status
    )


def main():
    """Точка входа: выбор режима работы программы."""
    print("Выберите режим работы:")
    print("  1 — автоматическая демонстрация сценария")
    print("  2 — интерактивная регистрация участника")

    mode = input("Номер режима (по умолчанию 1): ").strip()

    if mode == "2":
        run_interactive()
    else:
        run_demo()


if __name__ == "__main__":
    main()
