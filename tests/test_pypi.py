"""Проверки JSON API без доступа к внешней сети."""

import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pypi import PyPIRepository, parse_project


class PyPITests(unittest.TestCase):
    """Контракт HTTP и обработка метаданных PyPI."""

    def setUp(self):
        """Подготовить отдельный кэш для каждого теста."""
        self.repo = PyPIRepository("https://example.org")

    def test_read_and_cache(self):
        """Извлечь исходные строки и выполнить единственный запрос."""
        info = {"version": "1.0", "requires_dist": ["Other[extra]>=1"]}
        data = json.dumps({"info": info}).encode()
        with patch("pypi.urlopen", return_value=io.BytesIO(data)) as request:
            result = self.repo.project("Demo_Package")
            self.assertIs(result, self.repo.project("demo.package"))
        self.assertEqual(result.requirements, ("Other[extra]>=1",))
        request.assert_called_once()
        self.assertEqual(
            request.call_args.args[0].full_url,
            "https://example.org/pypi/demo-package/json",
        )

    def test_null_requirements(self):
        """Пустое поле считать отсутствием зависимостей."""
        result = parse_project({"info": {"version": "1", "requires_dist": None}})
        self.assertEqual(result.requirements, ())

    def test_network_errors(self):
        """Недоступный сервер и отсутствующий проект дают разные ошибки."""
        missing = HTTPError("https://example.org", 404, "Not found", {}, None)
        for error, message in ((missing, "отсутствует"), (URLError("X"), "прочитать")):
            with self.subTest(error=error):
                with patch("pypi.urlopen", side_effect=error):
                    with self.assertRaisesRegex(ValueError, message):
                        self.repo.project("demo")

    def test_invalid_response(self):
        """Некорректный JSON и структура метаданных дают диагностируемый сбой."""
        samples = ((b'!', "Некорректный JSON"), (b'{"info": []}', "метаданные"))
        for data, message in samples:
            with self.subTest(data=data):
                with patch("pypi.urlopen", return_value=io.BytesIO(data)):
                    with self.assertRaisesRegex(ValueError, message):
                        self.repo.project("demo")
