"""온톨로지(사람이 고정한 지식)가 스스로 맞는지: 끊어진 엣지가 없고, 문법 예가 실제 파이썬이고, 유형이 범위 15종 안에 있다."""

import unittest
from itertools import chain

from ..common.scope import ALGORITHMS
from ..knowledge import ontology as o

LANGUAGES = ("python", "java", "javascript", "cpp", "rust")


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
        got = o.pitfall_candidates(["dup_names", "없는_패턴"], ["pair_twice", "없는_함정"], "python")
        self.assertEqual(got[0], "pair_twice")
        self.assertIn("key_missing", got)
        self.assertNotIn("없는_함정", got)
        self.assertEqual(o.known_skills(["swap", "없는_기술"]), ["swap"])

    def test_syntax_examples_only_for_python(self):
        """문법 예는 파이썬으로만 써 두었다. 다른 언어의 튜터 지시에는 넣지 않는다."""
        self.assertEqual(len(o.skill_examples(["dict_count", "swap"], "python")), 2)
        for language in LANGUAGES:
            if language != "python":
                self.assertEqual(o.skill_examples(["dict_count", "swap"], language), [])

    def test_pitfalls_follow_the_language(self):
        python = o.pitfall_candidates([], [], "python")
        self.assertTrue({"missing_colon", "indent", "no_return"} <= set(python))
        for language in ("java", "javascript", "cpp", "rust"):
            got = o.pitfall_candidates([], ["missing_colon", "indent", "str_immutable"], language)
            self.assertFalse(o.PYTHON_ONLY & set(got), language)
            self.assertIn("no_return", got)  # 돌려주지 않는 실수는 다른 언어에도 있다
        self.assertNotIn("str_immutable", o.pitfall_candidates([], ["str_immutable"], "cpp"))
        self.assertIn("str_immutable", o.pitfall_candidates([], ["str_immutable"], "java"))

    def test_names_use_the_language_words(self):
        """그릇 이름은 언어마다 그 언어의 낱말이고, 파이썬에는 원래 글(구체 단서)이 그대로 간다. 모르는 언어는 중립 말."""
        self.assertEqual(o.technique_name("count_map", "python"), "개수 세기(딕셔너리)")
        self.assertEqual(o.technique_name("count_map", "java"), "개수 세기(HashMap)")
        self.assertEqual(o.technique_name("count_map", "cpp"), "개수 세기(map)")
        self.assertEqual(o.technique_name("count_map", "javascript"), "개수 세기(Map)")
        self.assertEqual(o.technique_name("count_map", ""), "개수 세기(키-값 표)")
        self.assertEqual(o.skill_name("dict_count", "python"), "딕셔너리로 개수 세기")
        self.assertEqual(o.skill_name("dict_count", "java"), "HashMap으로 개수 세기")
        self.assertEqual(o.skill_name("list_empty", "python"), "리스트가 비었는지 확인")
        self.assertEqual(o.skill_name("list_empty", "rust"), "배열이 비었는지 확인")
        self.assertEqual(o.pitfall_text("pop_front", "python"), ("리스트 앞에서 꺼내기", "pop(0)이나 insert(0)은 뒤의 것을 모두 민다"))
        self.assertEqual(o.pitfall_text("no_return", "python")[0], "돌려주지 않음(None)")
        self.assertEqual(o.pitfall_text("slow_search_in_loop", "python")[1], "반복마다 리스트 전체를 찾거나(in, count, index) 지운다")

    def test_other_languages_never_see_python_words(self):
        """파이썬이 아닌 언어에 가는 모든 이름·설명·단서에 파이썬 낱말이 없다."""
        words = ("리스트", "딕셔너리", "튜플", "pop(0)", "elif", "None", "(in, count", "//")
        for language in ("java", "javascript", "cpp", "rust", ""):
            shown = [o.technique_name(t, language) for t in o.TECHNIQUES] + [o.skill_name(s, language) for s in o.SKILLS]
            shown += [text for pid in o.PITFALLS if o.pitfall_fits(pid, language) for text in o.pitfall_text(pid, language)]
            shown += [text for _, _, why, seed in o.PATTERNS.values() for text in (why, seed)]
            shown += o.pattern_context(list(o.PATTERNS), language) + o.pitfall_lines(list(o.PITFALLS), language)
            shown += [o.technique_list(language), o.skill_list(language)]
            self.assertEqual([t for t in shown if any(w in t for w in words)], [], language)

    def test_context_lines_leave_out_pitfalls_the_language_lacks(self):
        """DFS 단서의 '자주 틀리는 것'과 함정 줄에 다른 언어가 없는 실수 이름을 붙이지 않는다."""
        dfs = [pid for pid, (_, tech, _, _) in o.PATTERNS.items() if tech == "dfs"] or list(o.PATTERNS)
        self.assertIn("돌려주지 않음(None)", " ".join(o.pattern_context(list(o.PATTERNS), "python")))
        self.assertNotIn("콜론", " ".join(o.pattern_context(list(o.PATTERNS), "java")))
        self.assertTrue(dfs)

    def test_context_lines_drop_pitfalls_the_language_lacks(self):
        """문자열 만들기 단서의 '자주 틀리는 것'에서 C++에는 없는 실수(문자열 글자 바꾸기)가 빠진다. 다른 언어에는 남는다."""
        build = [pid for pid, (_, tech, _, _) in o.PATTERNS.items() if tech == "string_build"]
        self.assertTrue(build)
        name = o.pitfall_text("str_immutable", "java")[0]
        self.assertIn(name, " ".join(o.pattern_context(build, "java")))
        self.assertNotIn(name, " ".join(o.pattern_context(build, "cpp")))


class PlanExampleTest(unittest.TestCase):
    def test_example_code_follows_the_language(self):
        from ..plan.prompts import example
        self.assertIn("count.get(title, 0)", example("python"))
        java = example("java")
        self.assertIn("getOrDefault", java)
        self.assertNotIn("for title in loans", java)
        for other in ("javascript", "cpp", "rust"):
            self.assertNotIn("count.get(title, 0)", example(other))
            self.assertNotIn("for title in loans", example(other))
        self.assertNotIn("reference", example("go"))  # 예가 없는 언어에는 지어내지 않는다
