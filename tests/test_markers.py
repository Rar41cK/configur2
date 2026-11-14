"""Проверки маркеров окружения и условных зависимостей."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from markers import Marker
from repositories import Dependency, parse_requirement


class MarkerTests(unittest.TestCase):
    """Проверить приоритет операций, версии и форму требований."""

    def setUp(self):
        """Зафиксировать окружение независимо от системы запуска."""
        self.values = {
            "python_version": "3.12",
            "sys_platform": "darwin",
            "extra": "",
        }

    def test_versions_and_precedence(self):
        """Сравнивать 3.12 и 3.9 численно и учитывать приоритет and."""
        marker = 'python_version > "3.9" or extra == "a" and extra == "b"'
        self.assertTrue(Marker(marker, self.values).evaluate())
        marker = '(python_version > "3.9" or extra == "a") and extra == "b"'
        self.assertFalse(Marker(marker, self.values).evaluate())

    def test_conditional_requirement(self):
        """Исключить неактивное ребро и сохранить extras активного."""
        self.assertIsNone(
            parse_requirement('colorama; sys_platform == "win32"', self.values)
        )
        result = parse_requirement(
            'Some_Package[EXTRA]>=1; sys_platform not in "linux win32"',
            self.values,
        )
        self.assertEqual(result, Dependency("some-package", ("extra",)))

    def test_direct_reference(self):
        """Не интерпретировать точку с запятой в URL как маркер."""
        url = "https://example.org/source;a=1"
        text = f'pkg @ {url} ; python_version == "3.*"'
        self.assertEqual(
            parse_requirement(text, self.values), Dependency("pkg")
        )

    def test_invalid_marker(self):
        """Выдать явную ошибку при неизвестном синтаксисе."""
        with self.assertRaises(ValueError):
            Marker('python_version > !', self.values).evaluate()
