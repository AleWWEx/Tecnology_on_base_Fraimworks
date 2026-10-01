"""Вспомогательные функции проекта.

Модуль собирает то, что используется в разных частях приложения:
безопасный ввод данных пользователя с обработкой исключений, функции
работы с датами и генерация следующего идентификатора записи.

Функции модуля остаются обычными функциями и на ПР3: ввод с клавиатуры
не относится к данным конкретного объекта, поэтому переносить его в
метод класса Club или Event было бы неверно.
"""

import datetime
from functools import wraps
from typing import Callable, Iterable, List, Sequence

DATE_FORMAT = "%d.%m.%Y"
DATE_FORMAT_HINT = "ДД.ММ.ГГГГ"
STORAGE_DATE_FORMAT = "%Y-%m-%d"

#: Журнал вызовов функций, помеченных декоратором logged.
CALL_LOG: List[str] = []


def logged(func: Callable) -> Callable:
    """Записывать имя функции в журнал перед её вызовом.

    Декоратор не меняет результат функции: он только запоминает
    вызов. functools.wraps сохраняет имя и документацию функции,
    поэтому интроспекция модуля продолжает работать.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        CALL_LOG.append(func.__name__)
        return func(*args, **kwargs)

    return wrapper


def get_call_log() -> List[str]:
    """Вернуть список имён вызванных функций журнала."""
    return list(CALL_LOG)


def clear_call_log() -> None:
    """Очистить журнал вызовов."""
    CALL_LOG.clear()


def input_text(prompt: str) -> str:
    """Запросить у пользователя непустую строку.

    Пустой ответ считается ошибочным, поэтому запрос повторяется до
    получения осмысленного значения.
    """
    while True:
        value = input(prompt).strip()
        if value != "":
            return value
        print("Ошибка ввода: значение не должно быть пустым.")


def input_int(prompt: str) -> int:
    """Запросить у пользователя целое число.

    При некорректном вводе выводится сообщение об ошибке, после чего
    запрос повторяется: исключение ValueError перехватывается внутри
    функции, программа не прерывается аварийно.
    """
    while True:
        value = input(prompt).strip()
        try:
            return int(value)
        except ValueError:
            print(f"Ошибка ввода: «{value}» не является целым числом.")


def input_date(prompt: str) -> datetime.date:
    """Запросить у пользователя дату в формате ДД.ММ.ГГГГ.

    При неверном формате выводится сообщение об ошибке, после чего
    запрос повторяется.
    """
    while True:
        value = input(prompt).strip()
        try:
            return parse_user_date(value)
        except ValueError:
            print(
                f"Ошибка ввода: дата «{value}» должна быть записана "
                f"в формате {DATE_FORMAT_HINT}."
            )


def input_choice(prompt: str, allowed: Sequence[str]) -> str:
    """Запросить у пользователя одно из допустимых значений.

    Регистр ввода не учитывается: ответ приводится к нижнему регистру.
    При недопустимом ответе запрос повторяется.
    """
    allowed_text = ", ".join(allowed)
    while True:
        value = input(f"{prompt} ({allowed_text}): ").strip().lower()
        if value in allowed:
            return value
        print(f"Ошибка ввода: введите одно из значений: {allowed_text}.")


def parse_user_date(value: str) -> datetime.date:
    """Преобразовать строку формата ДД.ММ.ГГГГ в объект date.

    При неверном формате выбрасывается исключение ValueError, которое
    перехватывает вызывающая функция ввода.
    """
    return datetime.datetime.strptime(value, DATE_FORMAT).date()


def parse_date(value: str) -> datetime.date:
    """Преобразовать строку формата ГГГГ-ММ-ДД в объект date.

    Такой формат используется при чтении дат из JSON-файлов проекта
    и при сохранении объектов Event обратно в файл.
    """
    return datetime.datetime.strptime(value, STORAGE_DATE_FORMAT).date()


def format_date(value: datetime.date) -> str:
    """Вернуть дату в виде строки ДД.ММ.ГГГГ для вывода пользователю."""
    return value.strftime(DATE_FORMAT)


def next_id(identifiers: Iterable[int]) -> int:
    """Вычислить идентификатор для новой записи коллекции.

    Принимается любая коллекция идентификаторов: в ПР2 это были ключи
    словарей, на ПР3 — атрибуты id объектов. Идентификаторы выдаются
    по возрастанию; пустая коллекция даёт первый идентификатор 1.
    """
    return max(identifiers, default=0) + 1
