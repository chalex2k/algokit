set dotenv-load

task := env("TASK")

all: create_tmp_file copy

copy:
  xclip -selection clipboard < tmp.py

create_tmp_file:
  python3 codegen.py

new DIR:
    @echo "Создание директории {{DIR}}..."
    mkdir -p "{{DIR}}"
    @echo "Копирование файла cf_example.py в директорию {{DIR}}..."
    cp cf_example.py "{{DIR}}/main.py"
    @echo "Запись переменной TASK={{DIR}}..."
    echo "TASK={{DIR}}" > .env
    @echo "Готово: файл cf_example.py скопирован в {{DIR}}, переменная окружения TASK установлена."

run_module: # по сути то же самое что и run
    python3 -m {{task}}.main

run:
    PYTHONPATH=. python3 {{task}}/main.py

test:
    python3 -m pytest {{task}}/main.py

test_files:
    python3 -m pytest -q test.py
