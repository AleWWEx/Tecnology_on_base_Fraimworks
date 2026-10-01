"""Вспомогательные функции проекта.

Модуль собирает то, что используется в разных частях приложения:
безопасный ввод данных пользователя с обработкой исключений, функции
работы с датами и генерация следующего идентификатора записи.
"""

import datetime
from typing import Sequence

DATE_FORMAT = "%d.%m.%Y"
DATE_FORMAT_HINT = "ДД.ММ.ГГГГ"
STORAGE_DATE_FORMAT = "%Y-%m-%d"


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

    Такой формат используется при чтении дат из JSON-файлов проекта.
    """
    return datetime.datetime.strptime(value, STORAGE_DATE_FORMAT).date()


def format_date(value: datetime.date) -> str:
    """Вернуть дату в виде строки ДД.ММ.ГГГГ для вывода пользователю."""
    return value.strftime(DATE_FORMAT)


def next_id(items: dict) -> int:
    """Вычислить идентификатор для новой записи словаря.

    Идентификаторы выдаются по возрастанию; пустой словарь даёт первый
    идентификатор 1.
    """
    return max(items, default=0) + 1
