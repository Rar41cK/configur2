"""Аргументы командной строки и проверка настроек проекта."""

import argparse
import re
from pathlib import Path
from urllib.parse import urlsplit

PYPI_URL = "https://pypi.org"
DISABLED_PORT = 0
PACKAGE_NAME = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
TEST_NAME = r"[A-Z]+"


def normalize(name):
    """Привести имя дистрибутива к форме, используемой в PyPI."""
    return re.sub(r"[-_.]+", "-", name).lower()


def validate_package(package, is_test):
    """Проверить имя пакета с учётом типа репозитория."""
    pattern = TEST_NAME if is_test else PACKAGE_NAME
    if not re.fullmatch(pattern, package):
        expected = "заглавные латинские буквы" if is_test else "имя PyPI"
        raise ValueError(f"--package: {package!r}, ожидается {expected}")


def validate_remote_url(repository):
    """Проверить базовый адрес сервера с PyPI JSON API."""
    try:
        url = urlsplit(repository)
        valid = (
            url.scheme in {"https", "http"}
            and url.hostname
            and url.port != DISABLED_PORT
        )
    except ValueError as error:
        raise ValueError("--repo: некорректный URL HTTP(S)") from error
    has_query_or_fragment = "?" in repository or "#" in repository
    if not valid or url.username is not None or has_query_or_fragment:
        raise ValueError(
            "--repo: укажите базовый URL HTTP(S) без учётных данных"
        )
    if any(character.isspace() for character in repository):
        raise ValueError("--repo: URL должен быть без пробельных символов")
    return repository.rstrip("/")


def validate_repository(repository, is_test):
    """Проверить путь к тестовому файлу или базовый URL JSON API."""
    if is_test:
        if not repository or not Path(repository).is_file():
            raise ValueError("--repo: укажите существующий тестовый файл")
        return repository
    return validate_remote_url(PYPI_URL if repository is None else repository)


def validate_output(output):
    """Проверить расширение и доступность каталога назначения."""
    if output.suffix.lower() != ".svg" or output.is_dir():
        raise ValueError("--output: укажите имя файла с расширением .svg")
    if not output.parent.is_dir():
        raise ValueError("--output: каталог назначения не существует")
    if output.with_suffix(".dot").is_dir():
        raise ValueError("--output: путь для DOT занят каталогом")


def make_parser():
    """Создать парсер с общими для всех этапов параметрами."""
    parser = argparse.ArgumentParser(description="Граф зависимостей PyPI")
    parser.add_argument("--package", required=True, help="имя пакета")
    parser.add_argument("--repo", help="базовый URL API или тестовый файл")
    parser.add_argument(
        "--test-repo", action="store_true", help="читать граф из файла"
    )
    parser.add_argument(
        "--output", type=Path, default=Path("dependencies.svg"),
        help="путь для SVG (по умолчанию dependencies.svg)",
    )
    return parser


def parse_args(argv=None):
    """Прочитать и проверить параметры перед выполнением операции."""
    parser = make_parser()
    args = parser.parse_args(argv)
    try:
        validate_package(args.package, args.test_repo)
        args.repo = validate_repository(args.repo, args.test_repo)
        validate_output(args.output)
        if args.test_repo:
            repository_path = Path(args.repo).resolve()
            outputs = (args.output, args.output.with_suffix(".dot"))
            if repository_path in {path.resolve() for path in outputs}:
                raise ValueError("--output: совпадает с тестовым репозиторием")
    except (ValueError, OSError, RuntimeError) as error:
        parser.error(str(error))
    if not args.test_repo:
        args.package = normalize(args.package)
    return args
