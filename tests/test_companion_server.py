from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from companion_server import CompanionServer, parse_problem, problem_directory_name


class CompanionServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        (self.root / "cf_example.py").write_text("def main():\n    pass\n")

        self.server = CompanionServer(("127.0.0.1", 0), self.root)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temporary_directory.cleanup()

    def post(self, payload: object):
        request = Request(
            self.base_url + "/",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        return urlopen(request)

    def test_imports_codeforces_problem(self) -> None:
        payload = {
            "name": "B. Example",
            "url": "https://codeforces.com/contest/2247/problem/B",
            "tests": [
                {"input": "3\n1 2 3\n", "output": "6\n"},
                {"input": "1\n9\n", "output": "9\n"},
            ],
        }

        with self.post(payload) as response:
            body = json.load(response)

        self.assertEqual(response.status, 200)
        self.assertEqual(body["directory"], "2247B")
        self.assertEqual(body["tests"], 2)
        self.assertEqual(
            (self.root / "2247B" / "main.py").read_text(),
            "def main():\n    pass\n",
        )
        self.assertEqual((self.root / "2247B" / "in1.txt").read_text(), "3\n1 2 3\n")
        self.assertEqual((self.root / "2247B" / "out2.txt").read_text(), "9\n")
        self.assertEqual((self.root / ".env").read_text(), "TASK=2247B\n")

    def test_does_not_overwrite_existing_task(self) -> None:
        task = self.root / "2247A"
        task.mkdir()
        (task / "main.py").write_text("my solution\n")
        payload = {
            "name": "A. Example",
            "url": "https://codeforces.com/problemset/problem/2247/A",
            "tests": [{"input": "1\n", "output": "2\n"}],
        }

        with self.assertRaises(HTTPError) as raised:
            self.post(payload)

        self.assertEqual(raised.exception.code, 409)
        self.assertEqual((task / "main.py").read_text(), "my solution\n")

    def test_uses_safe_problem_name_for_other_sites(self) -> None:
        problem = parse_problem(
            {
                "name": "A. Sum of Two Numbers",
                "url": "https://example.com/problems/a",
                "tests": [],
            }
        )
        self.assertEqual(problem_directory_name(problem), "A._Sum_of_Two_Numbers")

    def test_health_endpoint(self) -> None:
        with urlopen(self.base_url + "/health") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(json.load(response), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
