"""Источники рёбер графа для PyPI и локальных JSON-репозиториев."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from config import PACKAGE_NAME, TEST_NAME, normalize
from markers import Marker, environment
from pypi import PyPIRepository

REQUIREMENT = re.compile(rf"^\s*({PACKAGE_NAME})\s*(?:\[([^\]]+)\])?(.*)$")
URL_MARKER = re.compile(r"\s+;\s*", re.ASCII)


@dataclass(frozen=True)
class Dependency:
    """Имя зависимости и дополнительные возможности, указанные в ребре."""

    name: str
    extras: tuple[str, ...] = ()


def parse_requirement(text, values):
    """Извлечь имя и extras, если условие окружения выполняется."""
    match = REQUIREMENT.fullmatch(text)
    if not match:
        raise ValueError(f"Некорректный Requires-Dist: {text!r}")
    name, extras, tail = match.groups()
    if tail.lstrip().startswith("@"):
        marker = URL_MARKER.split(tail, maxsplit=1)[1:]
        marker = marker[0] if marker else ""
    else:
        marker = tail.partition(";")[2]
    if marker.strip() and not Marker(marker, values).evaluate():
        return None
    names = extras.split(",") if extras else ()
    normalized_extras = tuple(normalize(extra.strip()) for extra in names)
    return Dependency(normalize(name), normalized_extras)


class PyPISource:
    """Предоставить активные рёбра из метаданных последнего релиза."""

    def __init__(self, url):
        """Настроить API и зафиксировать окружение процесса."""
        self.repo = PyPIRepository(url)
        self.values = environment()

    def version(self, name):
        """Получить версию, указанную в метаданных PyPI."""
        return self.repo.project(name).version

    def dependencies(self, name, extra):
        """Прочитать зависимости пакета в контексте выбранной опции."""
        values = dict(self.values, extra=extra)
        for text in self.repo.project(name).requirements:
            try:
                dependency = parse_requirement(text, values)
            except (ValueError, SyntaxError) as error:
                raise ValueError(f"{name}: {error}") from error
            if dependency is not None:
                yield dependency


def load_repository(path):
    """Загрузить локальный JSON и проверить все ссылки между пакетами."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        message = f"Ошибка чтения тестового репозитория: {error}"
        raise ValueError(message) from error
    if not isinstance(data, dict):
        raise ValueError("Тестовый репозиторий должен быть JSON-объектом")
    for name, deps in data.items():
        if not re.fullmatch(TEST_NAME, name) or not isinstance(deps, list):
            raise ValueError(f"{name}: ожидается имя A–Z и массив зависимостей")
        if any(not isinstance(dep, str) or dep not in data for dep in deps):
            raise ValueError(f"{name}: все зависимости должны быть объявлены")
    return data


class LocalSource:
    """Предоставить рёбра из заранее заданного списка смежности."""

    def __init__(self, path):
        """Прочитать тестовый репозиторий."""
        self.data = load_repository(path)

    def version(self, name):
        """Проверить наличие имени, версия тестовым пакетам не нужна."""
        if name not in self.data:
            message = f"Пакет {name!r} отсутствует в тестовом репозитории"
            raise ValueError(message)
        return ""

    def dependencies(self, name, extra):
        """Последовательно вернуть зависимости тестового пакета."""
        return (Dependency(dep) for dep in self.data[name])
