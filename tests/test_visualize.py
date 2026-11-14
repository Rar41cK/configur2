"""Проверки DOT, интеграции с Graphviz и обработки ошибок."""

import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from graph import build_graph
from repositories import LocalSource
from visualize import render_svg, to_dot

SVG_NS = "{http://www.w3.org/2000/svg}"


class VisualizationTests(unittest.TestCase):
    """Проверить представление ациклических и циклических графов."""

    def test_dot_includes_back_edge_and_excludes_unreachable(self):
        """Сохранить обратное ребро, вывести только достижимые пакеты."""
        cycle = build_graph("A", LocalSource(PROJECT / "examples/cycle.json"))
        diamond_source = LocalSource(PROJECT / "examples/diamond.json")
        diamond = build_graph("A", diamond_source)
        self.assertIn('"C" -> "B";', to_dot(cycle))
        self.assertIn('"B" -> "D";', to_dot(diamond))
        self.assertNotIn('"E"', to_dot(diamond))

    def test_missing_graphviz(self):
        """Показать причину, если исполняемый файл dot не найден."""
        with patch("visualize.shutil.which", return_value=None):
            with self.assertRaisesRegex(ValueError, "Graphviz не найден"):
                render_svg("digraph {}")

    @unittest.skipUnless(shutil.which("dot"), "Требуется Graphviz")
    def test_cli_generates_svg(self):
        """Запустить CLI и проверить оба файла и диагностику цикла."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "cycle diagram.svg"
            result = subprocess.run(
                [
                    sys.executable, str(PROJECT / "src" / "main.py"),
                    "--package", "A", "--test-repo", "--repo",
                    str(PROJECT / "examples/cycle.json"),
                    "--output", str(output),
                ],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("B -> C -> B", result.stderr)
            svg = ET.parse(output).getroot()
            self.assertEqual(svg.tag, f"{SVG_NS}svg")
            self.assertIn('"C" -> "B";', output.with_suffix(".dot").read_text())
