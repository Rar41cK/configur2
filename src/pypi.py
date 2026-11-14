"""Чтение метаданных проектов через PyPI JSON API."""

import json
from dataclasses import dataclass
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from config import normalize

HTTP_NOT_FOUND = 404
TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class Project:
    """Опубликованная версия и её исходные строки Requires-Dist."""

    version: str
    requirements: tuple[str, ...]


def parse_project(data):
    """Проверить формат метаданных, ожидаемый от JSON API."""
    info = data["info"]
    requirements = info.get("requires_dist")
    if requirements is None:
        requirements = []
    if not isinstance(requirements, list):
        raise ValueError("requires_dist должен быть списком или null")
    if any(not isinstance(item, str) for item in requirements):
        raise ValueError("requires_dist должен содержать строки")
    version = info["version"]
    if not isinstance(version, str) or not version:
        raise ValueError("version должен быть непустой строкой")
    return Project(version, tuple(requirements))


class PyPIRepository:
    """Источник метаданных с кэшем на время одного анализа."""

    def __init__(self, base_url):
        """Сохранить базовый адрес API и создать пустой кэш."""
        self.base_url = base_url.rstrip("/")
        self.cache = {}

    def project(self, name):
        """Вернуть данные текущего релиза нормализованного имени."""
        name = normalize(name)
        if name not in self.cache:
            self.cache[name] = self.fetch(name)
        return self.cache[name]

    def fetch(self, name):
        """Получить и разобрать JSON одного проекта."""
        url = f"{self.base_url}/pypi/{quote(name, safe='')}/json"
        request = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                data = json.load(response)
        except HTTPError as error:
            if error.code == HTTP_NOT_FOUND:
                message = f"Пакет {name!r} отсутствует в репозитории"
                raise ValueError(message) from error
            raise ValueError(f"HTTP {error.code} при запросе {url}") from error
        except (URLError, OSError, HTTPException) as error:
            raise ValueError(f"Не удалось прочитать {url}: {error}") from error
        except (ValueError, UnicodeError) as error:
            raise ValueError(f"Некорректный JSON от {url}") from error
        try:
            return parse_project(data)
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            message = f"Неверные метаданные {name!r}: {error}"
            raise ValueError(message) from error
