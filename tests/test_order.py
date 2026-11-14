"""Проверки вывода порядка установки на этапе 4."""

import subprocess
import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


class OrderTests(unittest.TestCase):
    """Проверки завершения и результатов при запуске CLI."""

    def test_cli_order(self):
        """Общие зависимости, цикл и одиночная вершина."""
        cases = {
            "diamond": ("D -> B -> C -> A", ""),
            "cycle": ("D -> C -> B -> A", "Для цикла строгого порядка нет"),
            "leaf": ("A", ""),
        }
        for name, (order, warning) in cases.items():
            with self.subTest(repo=name):
                result = subprocess.run(
                    [
                        sys.executable, str(PROJECT / "src" / "main.py"),
                        "--package", "A", "--test-repo", "--repo",
                        str(PROJECT / "examples" / f"{name}.json"),
                    ],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), order)
                if warning:
                    self.assertIn(warning, result.stderr)
                else:
                    self.assertEqual(result.stderr, "")
