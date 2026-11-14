"""Проверки тестовых графов и правил обхода PyPI."""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))
from graph import build_graph
from pypi import Project
from repositories import LocalSource, PyPISource


class GraphTests(unittest.TestCase):
    """Проверить достижимость, слияние веток и циклы."""

    def load_graph(self, name, root="A"):
        """Загрузить один из демонстрационных тестовых репозиториев."""
        return build_graph(root, LocalSource(PROJECT / "examples" / name))

    def test_diamond(self):
        """Общая зависимость появляется один раз, другая ветка исключена."""
        graph = self.load_graph("diamond.json")
        self.assertEqual(list(graph.edges), ["A", "B", "D", "C"])
        self.assertEqual(list(graph.edges["C"]), ["D"])
        self.assertEqual(graph.cycles, [])

    def test_cycle(self):
        """Циклическое ребро сохраняется и не блокирует другие ветки."""
        graph = self.load_graph("cycle.json")
        self.assertEqual(graph.cycles, [("B", "C", "B")])
        self.assertEqual(list(graph.edges["C"]), ["B", "D"])

    def test_leaf_and_unknown_root(self):
        """Одиночная вершина и отсутствующее имя обрабатываются по-разному."""
        graph = self.load_graph("leaf.json")
        self.assertEqual(graph.edges, {"A": {}})
        with self.assertRaisesRegex(ValueError, "отсутствует"):
            self.load_graph("leaf.json", "Z")

    def test_undeclared_dependency(self):
        """Отклонить ссылку на несуществующий тестовый пакет."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "repo.json"
            path.write_text('{"A": ["B"]}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "объявлены"):
                LocalSource(path)

    def test_activated_extra(self):
        """Дополнительные зависимости объединяются с базовыми."""
        source = PyPISource("https://example.org")
        source.repo.cache.update({
            "root": Project("1", ("branch[fast]",)),
            "branch": Project("2", ('leaf; extra == "fast"',)),
            "leaf": Project("3", ()),
        })
        graph = build_graph("root", source)
        self.assertEqual(list(graph.edges["branch"]), ["leaf"])
        self.assertEqual(graph.versions["leaf"], "3")
