"""Точка входа для вывода порядка установки зависимостей."""

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
    """Показать зависимости перед зависящими от них пакетами."""
    args = parse_args(argv)
    try:
        graph = read_graph(args)
    except (ValueError, RecursionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    print_cycles(graph)
    if graph.cycles:
        print("Для цикла строгого порядка нет.", file=sys.stderr)
    print(" -> ".join(graph.postorder))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
