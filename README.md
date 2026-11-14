# Вариант 8. Граф зависимостей пакетов Python

Практическая работа по дисциплине «Конфигурационное управление».

Первый этап проверяет аргументы командной строки и выводит их в виде
`ключ=значение`. Требуется Python 3.9 или новее.

```sh
./run.sh --help
./run.sh --package requests --repo https://pypi.org --output requests.svg
python3 -m unittest discover -s tests -v
```

## Этап 2

`./run.sh --package requests` печатает все строки `Requires-Dist` из
JSON API PyPI, включая условные зависимости. Запросы делает `urllib`,
ответы читает `json`. Параметр `--repo` принимает базовый адрес сервера,
который отвечает на запросы вида `/pypi/имя/json`.

## Этап 3

Рекурсивный DFS раскрывает зависимости и сохраняет циклические рёбра.
Локальные репозитории описываются JSON-объектами с именами из заглавных
латинских букв. Достижимый граф выводится в виде списка смежности.

```sh
./run.sh --package A --test-repo --repo examples/diamond.json
./run.sh --package A --test-repo --repo examples/cycle.json
./run.sh --package A --test-repo --repo examples/leaf.json
```

## Этап 4

Пакет попадает в список при выходе из рекурсии DFS. В ациклическом графе
каждая зависимость стоит раньше пакета, которому она нужна. Для цикла
программа показывает обратное ребро и выводит порядок завершения DFS.

| Тестовый репозиторий | Результат для `A` |
| --- | --- |
| `diamond.json` | `D → B → C → A` |
| `cycle.json` | `D → C → B → A`, предупреждение о цикле `B → C → B` |
| `leaf.json` | `A` |

Сравнение с реальной установкой через pip 25.0.1 в отдельных каталогах
(`--target`), на macOS arm64 и CPython 3.12. Порядок pip взят из строки
`Installing collected packages`. Имена приведены к форме PyPI.

| Пакет | Порядок DFS | Порядок pip |
| --- | --- | --- |
| requests 2.34.2 | charset-normalizer → idna → urllib3 → certifi → requests | urllib3 → idna → charset-normalizer → certifi → requests |
| httpx 0.28.1 | idna → typing-extensions → anyio → certifi → h11 → httpcore → httpx | typing-extensions → idna → h11 → certifi → httpcore → anyio → httpx |
| pytest 9.2.0 | iniconfig → packaging → pluggy → pygments → pytest | pygments → pluggy → packaging → iniconfig → pytest |

Во всех трёх случаях набор пакетов совпал, и оба порядка удовлетворяют
всем рёбрам соответствующего графа. DFS следует за порядком
`Requires-Dist`. pip гарантирует установку зависимостей перед
зависящими от них пакетами и может произвольно упорядочить независимые
ветки. [Документация pip о порядке установки](https://pip.pypa.io/en/stable/cli/pip_install/#installation-order).
