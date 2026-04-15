# Переменная для пути к Python-скрипту
PYTHON_SCRIPT = codegen.py

# Цель по умолчанию, которая будет запускаться первой
all: full_process

# Цель для вызова Python-скрипта, создающего tmp.py
create_tmp_file:
	@echo "Запуск Python скрипта для создания tmp.py..."
	python3 $(PYTHON_SCRIPT)

# Цель для копирования содержимого tmp.py в буфер обмена с помощью pbcopy
copy_to_clipboard:
	@echo "Копирование содержимого tmp.py в буфер обмена..."
	pbcopy < tmp.py

# Цель для последовательного выполнения create_tmp_file и copy_to_clipboard
full_process: create_tmp_file copy_to_clipboard
	@echo "Процесс завершен: файл tmp.py создан и скопирован в буфер обмена."


# Цель для создания директории с параметром
new:
	@if [ -z "$(DIR)" ]; then \
		echo "Ошибка: Необходимо передать параметр DIR, например: make new DIR=my_directory"; \
		exit 1; \
	fi
	@echo "Создание директории $(DIR)..."
	mkdir -p $(DIR)
	@echo "Копирование файла cf_example.py в директорию $(DIR)..."
	cp cf_example.py $(DIR)/main.py
	@echo "Запись переменной TASK=$(DIR)..."
	echo "TASK=$(DIR)" > .env
	@echo "Готово: файл cf_example.py скопирован в $(DIR), переменная окружения TASK установлена."
