# Этап 1 — транспорт защищённой P2P-сети
Python 3.12+; основной код использует стандартную библиотеку. Из корня проекта:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -v
python scripts/run_demo.py
python scripts/benchmark.py
```
В PyCharm откройте папку проекта и выберите интерпретатор. Для ручной демонстрации в двух терминалах:

```sh
python main.py configs/node1.json serve
python main.py configs/node2.json ping
```
Первый процесс остановите Ctrl+C. Второй слушает собственный порт на время RPC. Для обратного направления поменяйте конфигурации местами. Порты 8001 и 8002 должны быть свободны. Журналы автоматической демонстрации и измерения находятся в results; повторный запуск перезаписывает их. Тесты проверены на Linux/Python 3.13.5, исходная версия затем проверена студентом на Windows и Python 3.12.3; v2 требует повторной проверки.

## Редакция v2 — Windows / PowerShell
На ПК студента используется `py`, а не `python`. Из корня проекта:
```powershell
py -m pip install -r requirements.txt
py -m unittest discover -v 2>&1 | Tee-Object results/tests_windows.log
py scripts/run_demo.py
py scripts/benchmark.py | Tee-Object results/benchmark_windows.json
```
Ожидается 12 успешных тестов. Сообщения NETWORK NEGATIVE, connection rejected и connection overload ожидаемы в отрицательных тестах. Скрипт demo читает обе конфигурации; при изменении портов согласуйте peer_port в обоих файлах. Можно указать альтернативные файлы через --node1 и --node2. Повторные запуски перезаписывают основные журналы: архивируйте их перед повтором.

## Git и сдача
В архиве поставляется локальный репозиторий с исходным коммитом редакции v2 (не утверждён преподавателем). После локальных испытаний проверьте `git status`, затем `git add .` и `git commit -m "Stage 1: Windows acceptance evidence"`. Если Git не установлен, установите Git for Windows. Покажите преподавателю ARCHITECTURE.md, PROTOCOL.md, ACCEPTANCE.md, журналы и `git log -1`. Зафиксируйте дату согласования и хеш утверждённого коммита. Если скрытая папка .git не извлеклась, выполните `git init`, `git add .`, `git commit -m "Stage 1 transport"` (при необходимости настройте собственные user.name и user.email).
