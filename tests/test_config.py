"""Проверки параметров командной строки."""

import subprocess
import sys
import tempfile
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

    def test_default_options(self):
        """Проверить параметры по умолчанию без обращения к сети."""
        result = self.run_cli("--package", "Foo_Bar")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("package=foo-bar", result.stdout)
        self.assertIn("repo=https://pypi.org", result.stdout)

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

    def test_existing_local_repository(self):
        """Принять тестовый файл с корректным именем пакета."""
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory) / "repo.json"
            repository.write_text('{"A": []}', encoding="utf-8")
            result = self.run_cli(
                "--package", "A", "--test-repo", "--repo", str(repository)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("test_repo=True", result.stdout)


if __name__ == "__main__":
    unittest.main()
