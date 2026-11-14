"""Точка входа визуализатора графа зависимостей."""

import sys

from config import parse_args
from graph import build_graph
from repositories import LocalSource, PyPISource
from visualize import save_graph


def read_graph(args):
    """Выбрать источник данных и построить граф."""
    source = LocalSource(args.repo) if args.test_repo else PyPISource(args.repo)
    return build_graph(args.package, source)


def print_cycles(graph):
    """Сообщить о найденных циклах через поток диагностики."""
    for cycle in graph.cycles:
        print("Цикл: " + " -> ".join(cycle), file=sys.stderr)


def main(argv=None):
    """Построить граф, сообщить о циклах и сохранить диаграмму."""
    args = parse_args(argv)
    try:
        graph = read_graph(args)
        print_cycles(graph)
        output_dot = save_graph(graph, args.output)
    except (ValueError, OSError, RecursionError) as error:
        print(f"Ошибка: {error}", file=sys.stderr)
        return 1
    print(f"DOT: {output_dot}")
    print(f"SVG: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
