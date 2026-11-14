"""에이전트 13개(A1–A13)와 단계 번호가 정해진 대로인지, 그래프 경계가 지켜지는지."""

import re
import unittest

from . import fakes
from ..main import AGENTS, graph

# 에이전트별 단계 수: A1 5, A2 2, A3 1, A4 5, A5 2, A6·A7 6, A8 3, A9 2, A10 4, A11 2, A12 3, A13 6(디버그)
DESIGN = {
    "ingest": 5, "context": 2, "request_check": 1, "plan": 8, "explain": 2, "chair": 6, "guide": 6,
    "followup": 3, "fill": 2, "feedback": 4, "debug": 6, "output_check": 2, "save": 3,
}


class DesignTest(unittest.TestCase):
    def test_every_agent_has_its_design_steps(self):
        import importlib

        for folder, count in DESIGN.items():
            with self.subTest(folder=folder):
                module = importlib.import_module(f"..{folder}.graph", __package__)
                compiled = module.graph()
                nodes = [n for n in compiled.get_graph().nodes if not n.startswith("__")]
                self.assertEqual(len(nodes), count, nodes)
                steps = getattr(module, "STEPS", None) or importlib.import_module("..turn.graph", __package__).STEPS
                self.assertEqual(set(steps.values()), set(nodes))

    def test_main_graph_has_agents_in_order(self):
        nodes = [n for n in graph().get_graph().nodes if not n.startswith("__")]
        self.assertEqual(nodes, list(AGENTS))

    def test_only_store_context_and_save_touch_sqlite(self):
        allowed = {"store", "context", "save", "tests"}  # knowledge/index.py(벡터)는 SQLite가 아니라 자기 파일을 쓴다
        for path in fakes.ROOT.rglob("*.py"):
            if allowed.intersection(path.relative_to(fakes.ROOT).parts):
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("sqlite3", text, path)
            self.assertNotRegex(text, r"(import|from)\s+fastapi", path)

    def test_imports_are_relative(self):
        """폴더째 옮겨도 돌게 tutor 안에서는 'tutor.'으로 시작하는 절대 import를 쓰지 않는다."""
        for path in fakes.ROOT.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(re.search(r"^\s*(from|import)\s+tutor\b", text, re.MULTILINE), path)
