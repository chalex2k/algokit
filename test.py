import importlib
import difflib
import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv


load_dotenv(".env")

task_dir = Path(os.getenv("TASK", "example"))

if str(task_dir) not in sys.path:
    sys.path.append(str(task_dir))

package = importlib.import_module("main")

RED = "\033[31m"
GREEN = "\033[32m"
RESET = "\033[0m"


def find_test_cases():
    if not task_dir.exists():
        return []

    return sorted(
        path
        for path in task_dir.iterdir()
        if path.is_file() and path.name.startswith("in")
    )


def expected_output_path(input_path):
    return input_path.with_name("out" + input_path.name[2:])


def run_main(input_path):
    old_stdin = sys.stdin
    old_stdout = sys.stdout
    output_path = task_dir / "tmp"

    try:
        with input_path.open("r") as fin, output_path.open("w") as fout:
            sys.stdin = fin
            sys.stdout = fout
            package.main()
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout

    return output_path.read_text()


def show_whitespace(text):
    return (
        text.replace(" ", "·")
        .replace("\t", "→")
        .replace("\r", "␍")
        .replace("\n", "↵\n")
    )


def colorize_diff(expected_content, found_content):
    expected_parts = []
    found_parts = []

    matcher = difflib.SequenceMatcher(None, expected_content, found_content)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        expected_part = show_whitespace(expected_content[i1:i2])
        found_part = show_whitespace(found_content[j1:j2])

        if tag == "equal":
            expected_parts.append(expected_part)
            found_parts.append(found_part)
        elif tag == "delete":
            expected_parts.append(f"{RED}{expected_part}{RESET}")
        elif tag == "insert":
            found_parts.append(f"{GREEN}{found_part}{RESET}")
        elif tag == "replace":
            expected_parts.append(f"{RED}{expected_part}{RESET}")
            found_parts.append(f"{GREEN}{found_part}{RESET}")

    return "".join(expected_parts), "".join(found_parts)


def format_failure(input_path, input_content, expected_content, found_content):
    expected_diff, found_diff = colorize_diff(expected_content, found_content)

    return (
        f"\nfile: {input_path.name}\n"
        f"\ninput:\n{input_content}"
        f"\nexpected:\n{expected_diff}"
        f"\nfound:\n{found_diff}"
    )


@pytest.mark.parametrize("input_path", find_test_cases(), ids=lambda path: path.name)
def test_code(input_path):
    output_path = expected_output_path(input_path)

    if not output_path.exists():
        pytest.fail(f"Не найден файл с ожидаемым ответом для {input_path.name}: {output_path.name}", pytrace=False)

    input_content = input_path.read_text()
    expected_content = output_path.read_text()
    found_content = run_main(input_path)

    if found_content != expected_content:
        pytest.fail(
            format_failure(
                input_path,
                input_content,
                expected_content,
                found_content,
            ),
            pytrace=False,
        )
