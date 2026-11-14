"""온톨로지(사람이 고정한 지식)가 스스로 맞는지: 끊어진 엣지가 없고, 문법 예가 실제 파이썬이고, 유형이 범위 15종 안에 있다."""

import unittest
from itertools import chain

from ..common.scope import ALGORITHMS
from ..knowledge import ontology as o


class OntologyTest(unittest.TestCase):
    def test_edges_point_to_existing_nodes(self):
        self.assertTrue(all(tech in o.TECHNIQUES for _, tech, _, _ in o.PATTERNS.values()))
        self.assertTrue(all(pid in o.PITFALLS for pid in chain(*o.PRONE_TO.values(), o.GENERAL)))
        self.assertEqual(set(o.PRONE_TO), set(o.TECHNIQUES))
        self.assertTrue(all(theme in ALGORITHMS for theme, _, _ in o.TECHNIQUES.values()))
        self.assertTrue(all(key in ALGORITHMS and set(before) <= set(ALGORITHMS) for key, before in o.PREREQUISITE.items()))
        self.assertTrue(all(kind in ("syntax", "runtime", "logic", "timeout") for kind, _, _, _ in o.PITFALLS.values()))

    def test_every_theme_has_a_clue(self):
        """15종 모두 문제 글에서 알아챌 단서가 하나는 있다."""
        covered = {o.TECHNIQUES[tech][0] for _, tech, _, _ in o.PATTERNS.values()}
        self.assertEqual(covered, set(ALGORITHMS))

    def test_skill_examples_are_real_python(self):
        for sid, (_, _, example) in o.SKILLS.items():
            last = example.rstrip().splitlines()[-1]
            body = example + ("\n" + " " * (len(last) - len(last.lstrip()) + 4) + "pass" if last.split("#")[0].rstrip().endswith(":") else "")
            with self.subTest(skill=sid):
                compile("def _f():\n" + "\n".join("    " + line for line in body.splitlines()), sid, "exec")

    def test_question_seeds_do_not_name_the_technique(self):
        """질문 씨앗은 의자가 쓸 수 있다. 기법 낱말이 들어가면 답을 주는 셈이다."""
        for pid, (_, tech, _, seed) in o.PATTERNS.items():
            for word in o.TECHNIQUES[tech][2]:
                self.assertFalse(o.has_term(word, seed), (pid, word))
            self.assertTrue(seed.endswith("?"), pid)

    def test_size_rule_narrows_methods(self):
        self.assertIn("이중 반복(N×N)이 된다", o.size_rule(1000))
        self.assertIn("이중 반복은 안 된다", o.size_rule(100_000))
        self.assertIn("한 번 훑기", o.size_rule(1_000_000))
        self.assertEqual(o.size_rule(0), "")

    def test_candidates_put_user_history_first_and_drop_unknown(self):
        got = o.pitfall_candidates(["dup_names", "없는_패턴"], ["pair_twice", "없는_함정"])
        self.assertEqual(got[0], "pair_twice")
        self.assertIn("key_missing", got)
        self.assertNotIn("없는_함정", got)
        self.assertEqual(o.known_skills(["swap", "없는_기술"]), ["swap"])
