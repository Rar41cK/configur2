# Вариант 8. Граф зависимостей пакетов Python

Практическая работа по дисциплине «Конфигурационное управление», ИКБО-13-25.
Программа читает `info.requires_dist` из JSON API PyPI, рекурсивно обходит
транзитивные зависимости и сохраняет граф в форматах DOT и SVG.
Вершина означает пакет. Стрелка `A → B` означает, что пакет `A` зависит от
`B`. Исходный пакет выделен цветом.

## Запуск

Требуется Python 3.9 или новее и Graphviz с командой `dot` в `PATH`.
Для PyPI нужен доступ к сети. Тестовые репозитории работают без сети.
Исходники запускаются напрямую, шаг сборки отсутствует.

```sh
./run.sh --help
mkdir -p build
./run.sh --package httpx --output build/httpx.svg
./run.sh --package A --test-repo --repo examples/cycle.json --output build/cycle.svg
python3 -m unittest discover -s tests -v
```

При необходимости укажи путь к интерпретатору через `PYTHON`, например
`PYTHON=python3.12 ./run.sh --package httpx`. При наличии `dot` тесты
проверяют запуск визуализации и структуру сгенерированного SVG.

| Параметр | Назначение |
| --- | --- |
| `--package` | Обязательное имя проекта PyPI. В тестовом режиме используются заглавные латинские буквы. |
| `--repo` | Базовый адрес HTTP(S) для запросов `/pypi/{имя}/json`. По умолчанию `https://pypi.org`. В тестовом режиме требуется путь к JSON. |
| `--test-repo` | Использовать локальное описание графа. Флаг передаётся без значения. |
| `--output` | Имя SVG в существующем каталоге. По умолчанию `dependencies.svg`. Рядом сохраняется файл с таким же именем и расширением `.dot`. |

Код выхода `2` означает неверные аргументы. Код `1` означает, что
не удалось выполнить анализ или записать результат. Найденный цикл
выводится в stderr, а его рёбра остаются в диаграмме.

## Исходники

| Модуль | Функции |
| --- | --- |
| `config.py` | Разбор аргументов, проверка путей, адреса и имён, нормализация имён PyPI. |
| `pypi.py` | HTTP-запрос, валидация метаданных и кэш версий и исходных строк зависимостей. |
| `markers.py` | Переменные окружения, разбор условий с группировкой, `and` и `or`, сравнение строк и числовых версий. |
| `repositories.py` | Извлечение имён и extras из требований, отбор активных зависимостей, загрузка тестового JSON. |
| `graph.py` | Рекурсивный DFS по достижимым пакетам и обнаружение обратных рёбер. |
| `visualize.py` | Формирование DOT, вызов `dot -Tsvg` и сохранение файлов. |
| `main.py` | Выбор источника, запуск обхода, диагностика и вывод путей к результатам. |

## Этапы работы

Каждому этапу соответствует коммит и тег `stage-1` … `stage-5`.
Историю можно посмотреть командой `git log --oneline --decorate`.
Для демонстрации отдельного этапа используй `git switch --detach stage-1`
или другой нужный тег. Вернуться к итоговой версии можно через
`git switch main`.

### Этап 1. Параметры CLI

```sh
./run.sh --package requests --repo https://pypi.org --output requests.svg
```

```text
package=requests
repo=https://pypi.org
test_repo=False
output=requests.svg
```

Следующие команды демонстрируют ошибки. Для каждой ожидается код выхода `2`.

```sh
./run.sh --package bad/name
./run.sh --package requests --repo ftp://pypi.org
./run.sh --package A --test-repo=false
./run.sh --package A --test-repo --repo missing.json
./run.sh --package requests --output graph.png
```

### Этап 2. Прямые зависимости PyPI

Команда `./run.sh --package requests` печатает исходные строки
`Requires-Dist`, включая условия окружения. Для получения данных
используются стандартные модули Python `urllib` и `json`.
[Описание PyPI JSON API](https://docs.pypi.org/api/json/).

### Этап 3. Транзитивный граф

```sh
./run.sh --package A --test-repo --repo examples/diamond.json
./run.sh --package A --test-repo --repo examples/cycle.json
./run.sh --package A --test-repo --repo examples/leaf.json
```

Тестовый JSON имеет форму `{"A": ["B"], "B": []}`. У каждого упомянутого
пакета есть собственный ключ. На этапе 3 программа выводит список
смежности. В «ромбе» сохраняются оба ребра к общей вершине `D`,
а недостижимая ветка `E → F` пропускается. В циклическом примере
сохраняется ребро `C → B` и выводится сообщение `Цикл: B -> C -> B`.
В третьем примере граф состоит только из вершины `A`.

### Этап 4. Порядок загрузки зависимостей

На теге `stage-4` для вывода порядка используются те же команды,
что в примерах этапа 3.


Порядок загрузки в этом этапе трактуется как план обработки зависимостей
перед зависящими от них пакетами. Пакет попадает в список при выходе из
рекурсии DFS. В ациклическом графе
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

В той же проверке pip скачивал файлы `.whl` в другом порядке.
Например, для `httpx` журнал скачивания колёс (без запросов
`.whl.metadata`) показал следующую последовательность.

```text
httpx → httpcore → anyio → idna → certifi → h11 → typing-extensions
```

pip загружает файлы по мере разрешения требований. Его гарантия порядка
относится к установке, а вывод этапа 4 показывает порядок, в котором
пакеты можно установить после разрешения зависимостей.
[Документация pip о разрешении зависимостей](https://pip.pypa.io/en/stable/topics/dependency-resolution/).

Исходные журналы контрольного запуска сохранены в
[docs/comparison](docs/comparison). В файлах `*-install.txt` видны
скачивание файлов и порядок установки. В `*-show.txt` приведены
версии и связи установленных пакетов. Эти результаты получены
14 ноября 2026 года на CPython 3.12 с pip 25.0.1.

### Этап 5. DOT и SVG

```sh
mkdir -p build
./run.sh --package requests --output build/requests.svg
./run.sh --package httpx --output build/httpx.svg
./run.sh --package pytest --output build/pytest.svg
```

Готовые диаграммы можно открыть в репозитории. [requests](docs/diagrams/requests.svg),
[httpx](docs/diagrams/httpx.svg) и [pytest](docs/diagrams/pytest.svg).
Исходники DOT лежат рядом. Состав графов проверен по полям `Name`,
`Version` и `Requires` команды `pip show` для каждого пакета
в той же контрольной установке, что на этапе 4. Каждая строка
`Requires` задаёт исходящие рёбра одной вершины. Оформление
и расположение стрелок обеспечивает Graphviz.
[Документация pip show](https://pip.pypa.io/en/stable/cli/pip_show/).

| Граф | Вершины | Рёбра | Сравнение с `pip show` |
| --- | ---: | ---: | --- |
| requests 2.34.2 | 5 | 4 | Имена, версии и рёбра совпали. |
| httpx 0.28.1 | 7 | 8 | Имена, версии и рёбра совпали. `certifi` и `idna` имеют по два входящих ребра. |
| pytest 9.2.0 | 5 | 4 | Имена, версии и рёбра совпали. Условия Windows и Python < 3.11 исключили неактивные рёбра. |

Встроенные команды pip предоставляют текстовые данные и JSON.
Отдельная команда рисования графов в перечне команд pip отсутствует.
Поэтому для сравнения изображений дополнительно использован сторонний
`pipdeptree 4.2.15`, запущенный на сохранённых контрольных установках.
Это выбранный способ выполнить сравнение для экосистемы pip.
[Перечень команд pip](https://pip.pypa.io/en/stable/cli/).
[Документация pipdeptree](https://github.com/tox-dev/pipdeptree).

| Пакет | Наш граф | Контрольный граф pipdeptree |
| --- | --- | --- |
| requests | [SVG](docs/diagrams/requests.svg) | [SVG](docs/diagrams/requests-pipdeptree.svg) |
| httpx | [SVG](docs/diagrams/httpx.svg) | [SVG](docs/diagrams/httpx-pipdeptree.svg) |
| pytest | [SVG](docs/diagrams/pytest.svg) | [SVG](docs/diagrams/pytest-pipdeptree.svg) |

Во всех трёх парах совпадают множества вершин и рёбер. В нашем графе
показаны имена и версии, а pipdeptree дополнительно подписывает рёбра
ограничениями версий. Различаются оформление и расположение вершин.
Файл `httpx-pipdeptree.svg` использует написание `typing_extensions`,
а наша программа нормализует его до `typing-extensions`.

Для повторения визуального сравнения после контрольной установки
установи pipdeptree в отдельное окружение. Его зависимости используются
только при сравнении. Код приложения получает зависимости через
стандартную библиотеку Python.

```sh
python3.12 -m venv build/comparison-env
build/comparison-env/bin/python -m pip install 'pipdeptree==4.2.15'
build/comparison-env/bin/python -m pipdeptree \
  --path "$PWD/build/pip-httpx" --packages httpx \
  --output graphviz-dot > build/httpx-pipdeptree.dot
dot -Tsvg build/httpx-pipdeptree.dot -o build/httpx-pipdeptree.svg
```

Для воспроизведения контрольной установки выполни команды в корне
репозитория с Python 3.12. Для двух остальных пакетов замени
`httpx` и список имён в последней строке.

```sh
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install 'pip==25.0.1'
mkdir -p build
python -m pip install --ignore-installed --only-binary=:all: \
  --index-url https://pypi.org/simple --target build/pip-httpx \
  --report build/pip-httpx.json httpx
PYTHONPATH="$PWD/build/pip-httpx" python -m pip show \
  httpx anyio certifi httpcore idna h11 typing-extensions
```

### Границы анализа PyPI

Утилита строит граф метаданных последнего релиза каждого пакета и учитывает
маркеры текущего окружения. Сравнение версий в маркерах поддерживает
числовые компоненты, но не полный синтаксис PEP 440. Для прямых ссылок
используется имя пакета и метаданные настроенного API. pip может выбрать
другую версию с учётом ограничений, доступных файлов и требований к Python,
поэтому на других пакетах или платформах результаты могут разойтись.
[Спецификация зависимостей](https://packaging.python.org/en/latest/specifications/dependency-specifiers/).

### Повторная проверка по заданию

21 ноября 2026 года проверены исходники и все пять этапов из истории Git.

| Требование | Проверка |
| --- | --- |
| CLI и четыре настройки | Тег `stage-1`, вывод настроек и ошибки параметров. |
| Прямые зависимости Python | Тег `stage-2`, запрос JSON API PyPI через `urllib`. |
| Рекурсивный DFS, транзитивность и циклы | Тег `stage-3`, примеры ромба, цикла и одиночной вершины. |
| Порядок загрузки | Тег `stage-4`, порядок завершения DFS и сравнение с журналами pip. |
| DOT и SVG для трёх пакетов | Итоговая версия, `docs/diagrams` и сравнение с pip show и pipdeptree. |
| История разработки | Отдельные коммиты и теги `stage-1` … `stage-5`. |
| Правила оформления кода | Длины файлов и функций, аргументы, docstring, имена и сложность. |

Функция проверки адреса выделена из проверки типа репозитория.
По результату Radon сложность каждой функции итоговых исходников
и тестов не превышает 10. Файлы Python содержат не более 80 символов
в строке, функции занимают не более 40 строк и имеют не более
7 объявленных аргументов. Сторонние инструменты аудита устанавливались
за пределами репозитория.
