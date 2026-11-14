"""Точка входа для вывода прямых зависимостей PyPI."""

import sys

from config import parse_args
from pypi import PyPIRepository


def main(argv=None):
    """Вывести строки Requires-Dist заявленные в метаданных пакета."""
    args = parse_args(argv)
    try:
        if args.test_repo:
            raise ValueError("тестовый репозиторий будет доступен на этапе 3")
        project = PyPIRepository(args.repo).project(args.package)
    except ValueError as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    print(f"{args.package} {project.version}")
    for requirement in project.requirements:
        print(requirement)
    if not project.requirements:
        print("Нет прямых зависимостей")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
