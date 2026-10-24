set dotenv-load

task := env("TASK")

all: create_tmp_file copy

copy:
  xclip -selection clipboard < tmp.py

create_tmp_file:
  python3 codegen.py

new DIR:
    python3 task_setup.py "{{DIR}}"

companion PORT="10043":
    python3 companion_server.py --port "{{PORT}}"

run_module: # по сути то же самое что и run
    python3 -m {{task}}.main

run:
    PYTHONPATH=. python3 {{task}}/main.py

test:
    python3 -m pytest {{task}}/main.py

test_files:
    python3 -m pytest -q test.py
