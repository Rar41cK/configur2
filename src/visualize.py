"""Преобразование графа в DOT и сохранение диаграммы Graphviz."""

import shutil
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

RENDER_TIMEOUT = 30


def quote(text):
    """Экранировать имя или подпись для строкового литерала DOT."""
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    text = text.replace("\r", "").replace("\n", "\\n")
    return f'"{text}"'


def to_dot(graph):
    """Записать вершины, версии пакетов и направленные рёбра."""
    lines = [
        "strict digraph dependencies {",
        '  graph [rankdir=LR, bgcolor="white", pad=0.18, nodesep=0.33];',
        '  node [shape=box, style="rounded,filled", fontname="Helvetica",',
        '        color="#B8C6D5", fillcolor="#F2F6FA", fontcolor="#182A3B"];',
        '  edge [color="#52708C", arrowsize=0.7];',
    ]
    for name in graph.edges:
        version = graph.versions[name]
        label = quote(f"{name}\n{version}" if version else name)
        attrs = f"label={label}"
        if name == graph.root:
            attrs += ', fillcolor="#1D4B72", fontcolor="white", color="#1D4B72"'
        lines.append(f"  {quote(name)} [{attrs}];")
    for name, dependencies in graph.edges.items():
        for dependency in dependencies:
            lines.append(f"  {quote(name)} -> {quote(dependency)};")
    return "\n".join([*lines, "}", ""])


def render_svg(dot_source):
    """Вызвать Graphviz, передавая DOT через стандартный ввод."""
    dot = shutil.which("dot")
    if dot is None:
        raise ValueError(
            "Graphviz не найден: установите dot и добавьте его в PATH"
        )
    try:
        result = subprocess.run(
            [dot, "-Tsvg"], input=dot_source.encode("utf-8"),
            capture_output=True, check=True, timeout=RENDER_TIMEOUT,
        )
    except subprocess.TimeoutExpired as error:
        raise ValueError("Graphviz не завершил обработку вовремя") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", errors="replace").strip()
        message = f"Ошибка Graphviz: {detail or error.returncode}"
        raise ValueError(message) from error
    return result.stdout


def write_file(path, data):
    """Заменить файл только после успешной записи его содержимого."""
    with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
            stream.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def save_graph(graph, output):
    """Сохранить SVG и исходный DOT рядом с ним."""
    output_dot = output.with_suffix(".dot")
    source = to_dot(graph)
    svg = render_svg(source)
    write_file(output_dot, source.encode("utf-8"))
    write_file(output, svg)
    return output_dot
