"""Построение графа рекурсивным DFS и поиск обратных рёбер."""

from dataclasses import dataclass, field


@dataclass
class Graph:
    """Список смежности, метаданные и циклы достижимых пакетов."""

    root: str
    edges: dict = field(default_factory=dict)
    versions: dict = field(default_factory=dict)
    cycles: list = field(default_factory=list)
    postorder: list = field(default_factory=list)


def collect(graph, source):
    """Раскрыть зависимости рекурсивно, учитывая контексты extras."""
    expanded = set()

    def visit(name, extra):
        """Один раз раскрыть пару из имени пакета и имени extra."""
        context = (name, extra)
        if context in expanded:
            return
        expanded.add(context)
        if name not in graph.edges:
            graph.edges[name] = {}
            graph.versions[name] = source.version(name)
        for dependency in source.dependencies(name, extra):
            graph.edges[name][dependency.name] = None
            visit(dependency.name, "")
            for requested_extra in dependency.extras:
                visit(dependency.name, requested_extra)

    visit(graph.root, "")


def scan(graph):
    """Найти циклы и записать вершины при выходе из рекурсии."""
    finished, active, path = set(), {}, []

    def visit(name):
        """Зафиксировать цикл при повторном посещении активной вершины."""
        if name in active:
            cycle = (*path[active[name]:], name)
            if cycle not in graph.cycles:
                graph.cycles.append(cycle)
            return
        if name in finished:
            return
        active[name] = len(path)
        path.append(name)
        for dependency in graph.edges[name]:
            visit(dependency)
        path.pop()
        del active[name]
        finished.add(name)
        graph.postorder.append(name)

    visit(graph.root)


def build_graph(root, source):
    """Собрать граф, достижимый из заданного пакета."""
    graph = Graph(root)
    collect(graph, source)
    scan(graph)
    return graph
