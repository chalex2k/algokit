from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def _task_path(root: Path, task_name: str) -> Path:
    if not task_name or "\n" in task_name or "\r" in task_name:
        raise ValueError("Имя директории задачи не может быть пустым")

    relative_path = Path(task_name)
    invalid_part = any(part in {"", ".", ".."} for part in relative_path.parts)
    if relative_path.is_absolute() or invalid_part:
        raise ValueError(f"Недопустимое имя директории задачи: {task_name!r}")

    root = root.resolve()
    task_path = (root / relative_path).resolve(strict=False)
    if not task_path.is_relative_to(root) or task_path == root:
        raise ValueError(f"Директория задачи должна находиться внутри {root}")

    return task_path


def create_task(root: Path, task_name: str, *, overwrite: bool = True) -> Path:
    """Create the same files as ``just new`` and update .env."""
    root = root.resolve()
    task_path = _task_path(root, task_name)

    print(f"Создание директории {task_name}...")
    task_path.mkdir(parents=True, exist_ok=overwrite)

    template_path = root / "cf_example.py"
    if not template_path.is_file():
        raise FileNotFoundError(f"Не найден шаблон: {template_path}")

    print(f"Копирование файла cf_example.py в директорию {task_name}...")
    shutil.copyfile(template_path, task_path / "main.py")

    print("Создание пустых файлов in1.txt и out1.txt...")
    (task_path / "in1.txt").touch()
    (task_path / "out1.txt").touch()

    relative_task_path = task_path.relative_to(root).as_posix()
    print(f"Запись переменной TASK={relative_task_path}...")
    (root / ".env").write_text(f"TASK={relative_task_path}\n", encoding="utf-8")

    print(
        f"Готово: в {relative_task_path} созданы main.py, in1.txt и out1.txt, "
        "переменная окружения TASK установлена."
    )
    return task_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Создать каталог новой задачи")
    parser.add_argument("directory", help="имя каталога задачи")
    args = parser.parse_args()
    create_task(ROOT, args.directory)


if __name__ == "__main__":
    main()
