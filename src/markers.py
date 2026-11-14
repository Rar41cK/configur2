"""Разбор маркеров окружения Requires-Dist стандартной библиотекой."""

import ast
import operator
import os
import platform
import re
import sys

TOKEN = re.compile(
    r"""\s*("[^"]*"|'[^']*'|===|~=|==|!=|<=|>=|[<>()]|[a-zA-Z_]\w*)"""
)
OPERATORS = {
    "==": operator.eq, "!=": operator.ne, "<": operator.lt,
    "<=": operator.le, ">": operator.gt, ">=": operator.ge,
}
VERSION_FIELDS = {
    "python_version", "python_full_version", "implementation_version",
}
RELEASE = re.compile(r"\d+(?:\.\d+)*")


def environment():
    """Собрать значения стандартных переменных маркеров PEP 508."""
    return {
        "implementation_name": sys.implementation.name,
        "implementation_version": platform.python_version(),
        "os_name": os.name,
        "platform_machine": platform.machine(),
        "platform_python_implementation": platform.python_implementation(),
        "platform_release": platform.release(),
        "platform_system": platform.system(),
        "platform_version": platform.version(),
        "python_full_version": platform.python_version(),
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "sys_platform": sys.platform,
    }


def tokenize(marker):
    """Распознать литералы, имена, операторы и скобки."""
    offset = 0
    marker = marker.strip()
    while offset < len(marker):
        match = TOKEN.match(marker, offset)
        if match is None:
            raise ValueError(f"Некорректный маркер: {marker!r}")
        yield match[1]
        offset = match.end()


def release_parts(value):
    """Разобрать числовую версию для обычных маркеров Python."""
    if not RELEASE.fullmatch(value):
        raise ValueError(f"Неподдерживаемая версия в маркере: {value!r}")
    return tuple(int(part) for part in value.split("."))


def compare_release(left, right, operation):
    """Сравнить версии численно с выравниванием нулевыми компонентами."""
    if operation in {"==", "!="} and right.endswith(".*"):
        prefix = release_parts(right.removesuffix(".*"))
        values = release_parts(left) + (0,) * len(prefix)
        return (values[:len(prefix)] == prefix) == (operation == "==")
    left_parts, right_parts = release_parts(left), release_parts(right)
    size = max(len(left_parts), len(right_parts))
    left_parts += (0,) * (size - len(left_parts))
    right_parts += (0,) * (size - len(right_parts))
    if operation == "~=":
        count = len(release_parts(right)) - 1
        if not count:
            raise ValueError("Для ~= необходимы хотя бы два компонента версии")
        same_prefix = left_parts[:count] == right_parts[:count]
        return left_parts >= right_parts and same_prefix
    return OPERATORS[operation](left_parts, right_parts)


class Marker:
    """Вычислить условие с приоритетом скобок, and и or."""

    def __init__(self, source, values):
        """Подготовить последовательность токенов и значения переменных."""
        self.tokens = iter(tokenize(source))
        self.current = next(self.tokens, None)
        self.values = values

    def take(self):
        """Перейти к следующему токену."""
        token = self.current
        self.current = next(self.tokens, None)
        return token

    def accept(self, token):
        """Поглотить токен, если он совпадает с ожидаемым."""
        if self.current != token:
            return False
        self.take()
        return True

    def evaluate(self):
        """Вычислить выражение и проверить, что разобраны все токены."""
        result = self.disjunction()
        if self.current is not None:
            raise ValueError(f"Неожиданный токен маркера: {self.current!r}")
        return result

    def disjunction(self):
        """Разобрать цепочку операций or."""
        result = self.conjunction()
        while self.accept("or"):
            other = self.conjunction()
            result = result or other
        return result

    def conjunction(self):
        """Разобрать цепочку операций and."""
        result = self.term()
        while self.accept("and"):
            other = self.term()
            result = result and other
        return result

    def term(self):
        """Разобрать сравнение или вложенное выражение."""
        if self.accept("("):
            result = self.disjunction()
            if not self.accept(")"):
                raise ValueError("В маркере отсутствует закрывающая скобка")
            return result
        left_token = self.take()
        operation = self.take()
        if operation == "not" and self.accept("in"):
            operation = "not in"
        return self.compare(left_token, operation, self.take())

    def operand(self, token):
        """Получить строковый литерал или значение переменной."""
        if token and token.startswith(("'", '"')):
            return ast.literal_eval(token)
        if token not in self.values:
            raise ValueError(f"Неизвестная переменная маркера: {token!r}")
        return self.values[token]

    def compare(self, left_token, operation, right_token):
        """Сравнить строки или числовые версии согласно типу поля."""
        left, right = self.operand(left_token), self.operand(right_token)
        if operation == "in":
            return left in right
        if operation == "not in":
            return left not in right
        if operation == "===":
            return left == right
        version = {left_token, right_token} & VERSION_FIELDS
        if version and operation in (*OPERATORS, "~="):
            return compare_release(left, right, operation)
        if operation not in OPERATORS:
            raise ValueError(f"Неподдерживаемый оператор: {operation!r}")
        return OPERATORS[operation](left, right)
