"""Проверки параметров командной строки."""

import subprocess
import sys
import unittest
from pathlib import Path

MAIN = Path(__file__).resolve().parents[1] / "src" / "main.py"


class ConfigTests(unittest.TestCase):
    """Проверки аргументов на уровне запуска программы."""

    def run_cli(self, *args):
        """Запустить программу с указанными параметрами."""
        return subprocess.run(
            [sys.executable, str(MAIN), *args], capture_output=True, text=True
        )

    def test_invalid_options(self):
        """Каждый параметр имеет сценарий ошибки."""
        examples = (
            (("--package", "bad/name"), "--package"),
            (("--repo", "ftp://example.org"), "--repo"),
            (("--repo", "https://example.org:99999"), "--repo"),
            (("--test-repo=false",), "--test-repo"),
            (("--test-repo",), "--repo"),
            (("--output", "graph.png"), "--output"),
        )
        for options, name in examples:
            with self.subTest(options=options):
                result = self.run_cli("--package", "A", *options)
                self.assertEqual(result.returncode, 2)
                self.assertIn(name, result.stderr)


class URLValidationTests(unittest.TestCase):
    """Проверить обработку URL без обращения к серверу."""

    @classmethod
    def setUpClass(cls):
        """Загрузить модуль конфигурации из исходников."""
        sys.path.insert(0, str(MAIN.parent))
        import config
        cls.config = config

    def test_valid_url_and_defaults(self):
        """Сохранить адрес зеркала и нормализовать имя пакета."""
        args = self.config.parse_args([
            "--package", "Foo_Bar", "--repo", "https://example.org/api/",
        ])
        self.assertEqual(args.package, "foo-bar")
        self.assertEqual(args.repo, "https://example.org/api")
        self.assertEqual(args.output, Path("dependencies.svg"))

    def test_invalid_url_forms(self):
        """Отклонить ошибки адреса после разделения валидации."""
        samples = (
            "", "ftp://host", "https://[", "https://host:abc",
            "https://host:0", "https://host?", "https://host#",
            "https://user:pass@host", "https://bad host",
        )
        for url in samples:
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    self.config.validate_remote_url(url)


if __name__ == "__main__":
    unittest.main()
