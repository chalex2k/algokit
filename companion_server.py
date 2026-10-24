from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from task_setup import ROOT, create_task


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 10043
MAX_REQUEST_SIZE = 10 * 1024 * 1024


class PayloadError(ValueError):
    pass


class TaskAlreadyExistsError(FileExistsError):
    pass


@dataclass(frozen=True)
class Sample:
    input: str
    output: str


@dataclass(frozen=True)
class Problem:
    name: str
    url: str
    tests: tuple[Sample, ...]


def parse_problem(data: Any) -> Problem:
    if not isinstance(data, dict):
        raise PayloadError("JSON-запрос должен содержать объект")

    name = data.get("name")
    url = data.get("url")
    tests = data.get("tests")

    if not isinstance(name, str) or not name.strip():
        raise PayloadError("Поле name должно быть непустой строкой")
    if not isinstance(url, str) or not url.strip():
        raise PayloadError("Поле url должно быть непустой строкой")
    if not isinstance(tests, list):
        raise PayloadError("Поле tests должно быть массивом")

    parsed_tests: list[Sample] = []
    for index, test in enumerate(tests, start=1):
        if not isinstance(test, dict):
            raise PayloadError(f"tests[{index - 1}] должен быть объектом")
        sample_input = test.get("input")
        sample_output = test.get("output")
        if not isinstance(sample_input, str) or not isinstance(sample_output, str):
            raise PayloadError(
                f"Поля input и output в tests[{index - 1}] должны быть строками"
            )
        parsed_tests.append(Sample(input=sample_input, output=sample_output))

    return Problem(name=name.strip(), url=url.strip(), tests=tuple(parsed_tests))


def problem_directory_name(problem: Problem) -> str:
    parsed_url = urlsplit(problem.url)
    host = (parsed_url.hostname or "").lower()
    path = parsed_url.path.rstrip("/")

    if host == "codeforces.com" or host.endswith(".codeforces.com"):
        match = re.search(
            r"/(?:contest|gym)/(\d+)/problem/([A-Za-z0-9]+)$",
            path,
        )
        if match is None:
            match = re.search(
                r"/problemset/problem/(\d+)/([A-Za-z0-9]+)$",
                path,
            )
        if match is not None:
            contest_id, problem_index = match.groups()
            return f"{contest_id}{problem_index.upper()}"

    safe_name = re.sub(r"[^\w.-]+", "_", problem.name, flags=re.UNICODE)
    safe_name = safe_name.strip("._-")[:100]
    if not safe_name:
        raise PayloadError("Не удалось получить имя директории из полей name и url")
    return safe_name


def import_problem(root: Path, problem: Problem) -> Path:
    directory_name = problem_directory_name(problem)
    task_path = root / directory_name
    if task_path.exists():
        raise TaskAlreadyExistsError(
            f"Каталог {directory_name} уже существует; main.py не был перезаписан"
        )

    task_path = create_task(root, directory_name, overwrite=False)
    for index, sample in enumerate(problem.tests, start=1):
        (task_path / f"in{index}.txt").write_text(sample.input, encoding="utf-8")
        (task_path / f"out{index}.txt").write_text(sample.output, encoding="utf-8")

    return task_path


class CompanionServer(HTTPServer):
    def __init__(self, server_address: tuple[str, int], root: Path):
        super().__init__(server_address, CompanionRequestHandler)
        self.root = root.resolve()


class CompanionRequestHandler(BaseHTTPRequestHandler):
    server: CompanionServer

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_common_headers(content_length=0)
        self.end_headers()

    def do_GET(self) -> None:
        if self.path != "/health":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        self._send_json(HTTPStatus.OK, {"status": "ok"})

    def do_POST(self) -> None:
        if self.path != "/":
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        try:
            content_length = self._content_length()
            raw_body = self.rfile.read(content_length)
            data = json.loads(raw_body.decode("utf-8"))
            problem = parse_problem(data)
            task_path = import_problem(self.server.root, problem)
        except TaskAlreadyExistsError as error:
            self._send_json(HTTPStatus.CONFLICT, {"error": str(error)})
            return
        except (PayloadError, UnicodeDecodeError, json.JSONDecodeError) as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        except ValueError as error:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        except Exception as error:
            print(f"Ошибка импорта задачи: {error}")
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": "не удалось создать файлы задачи"},
            )
            return

        relative_path = task_path.relative_to(self.server.root).as_posix()
        print(
            f"Получена задача {problem.name!r}: {len(problem.tests)} "
            f"sample-тест(ов), каталог {relative_path}"
        )
        self._send_json(
            HTTPStatus.OK,
            {
                "status": "ok",
                "directory": relative_path,
                "tests": len(problem.tests),
            },
        )

    def _content_length(self) -> int:
        raw_content_length = self.headers.get("Content-Length")
        if raw_content_length is None:
            raise PayloadError("Отсутствует заголовок Content-Length")
        try:
            content_length = int(raw_content_length)
        except ValueError as error:
            raise PayloadError("Некорректный Content-Length") from error
        if content_length < 0 or content_length > MAX_REQUEST_SIZE:
            raise PayloadError(
                f"Размер запроса должен быть не больше {MAX_REQUEST_SIZE} байт"
            )
        return content_length

    def _send_json(self, status: HTTPStatus, data: dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._send_common_headers(content_length=len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_common_headers(self, *, content_length: int) -> None:
        self.send_header("Content-Length", str(content_length))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.client_address[0]} - {format % args}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Локальный сервер для Competitive Companion"
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    server = CompanionServer((DEFAULT_HOST, args.port), ROOT)
    print(f"Competitive Companion listener: http://{DEFAULT_HOST}:{args.port}/")
    print("Откройте задачу в браузере и нажмите кнопку Competitive Companion.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
