"""저장소 구조 시험: 큰 구조(app/ · Docs/ · README)가 그대로인지, 내부 파일이 추적되지 않는지 본다. 표준 라이브러리만 쓴다.

실행: cd app && python3 ui/test_structure.py
"""

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_ALLOWED = {"README.md", "LICENSE", ".gitignore", ".env.example", ".github", "app", "Docs"}
APP_ALLOWED = {"ui", "tutor", "judge", "llm", "packaging", "README.md", "__init__.py"}  # __init__.py: 저장소 루트에서 app.llm으로 부른다
DOCS_ALLOWED = {"README.md", "guide", "architecture", "contributing", "THIRD_PARTY_NOTICES.md"}
INTERNAL = {"local_docs", "agents.md", "agent.md", "claude.md", "gemini.md", ".mcp.json", ".env", "memo.md"}


def tracked() -> list[str]:
    out = subprocess.run(["git", "-C", str(ROOT), "-c", "core.quotepath=off", "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
    return [path for path in out.split("\0") if path]


def children(paths: list[str], folder: str) -> set[str]:
    return {path[len(folder) + 1:].split("/")[0] for path in paths if path.startswith(folder + "/")}


class Structure(unittest.TestCase):
    paths = tracked()

    def test_root(self):
        self.assertLessEqual({path.split("/")[0] for path in self.paths}, ROOT_ALLOWED)

    def test_app(self):
        self.assertLessEqual(children(self.paths, "app"), APP_ALLOWED)

    def test_docs(self):
        self.assertLessEqual(children(self.paths, "Docs"), DOCS_ALLOWED)

    def test_no_internal_files(self):
        found = [path for path in self.paths if INTERNAL.intersection(part.lower() for part in path.split("/"))]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
