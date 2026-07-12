from dotenv import load_dotenv
import os



def replace_import_with_content(source_file, insert_file, output_file):
    try:
        # Чтение первого файла
        with open(source_file, 'r', encoding='utf-8') as src:
            source_lines = src.readlines()

        # Чтение второго файла
        with open(insert_file, 'r', encoding='utf-8') as ins:
            insert_content = ins.read()

        # Замена строки "from fastio.main import *" на содержимое второго файла
        updated_lines = []
        for line in source_lines:
            if line.strip() == "from fastio.main import *":
                updated_lines.append(insert_content)  # Вставка содержимого
            else:
                updated_lines.append(line)

        # Запись результата в выходной файл
        with open(output_file, 'w', encoding='utf-8') as out:
            out.writelines(updated_lines)

        print(f"Файл успешно обновлён и сохранён в {output_file}")

    except Exception as e:
        print(f"Ошибка: {e}")


# Пример использования
if __name__ == "__main__":
    load_dotenv(".env")

    # var_name1 = os.getenv("VAR_NAME1")
    task_dir = os.getenv("TASK", "example")  # Default value
    # if len(sys.argv) != 4:
    #     print("Использование: python script.py <source_file> <insert_file> <output_file>")
    # else:
        # source_file = sys.argv[1]
        # insert_file = sys.argv[2]
        # output_file = sys.argv[3]

    source_file = task_dir + '/main.py'
    insert_file = 'fastio/main.py'
    output_file = 'tmp.py'
    replace_import_with_content(source_file, insert_file, output_file)
