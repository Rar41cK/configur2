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
