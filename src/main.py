"""Точка входа анализатора транзитивных зависимостей."""

import sys

from config import parse_args
from graph import build_graph
from repositories import LocalSource, PyPISource


def read_graph(args):
    """Выбрать источник данных и построить граф."""
    source = LocalSource(args.repo) if args.test_repo else PyPISource(args.repo)
    return build_graph(args.package, source)


def print_cycles(graph):
    """Сообщить о найденных циклах через поток диагностики."""
    for cycle in graph.cycles:
        print("Цикл: " + " -> ".join(cycle), file=sys.stderr)


def main(argv=None):
    """Построить граф и показать список смежности."""
    args = parse_args(argv)
    try:
        graph = read_graph(args)
    except (ValueError, RecursionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    print_cycles(graph)
    for name, dependencies in graph.edges.items():
        print(f"{name}: {', '.join(dependencies) or '∅'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
