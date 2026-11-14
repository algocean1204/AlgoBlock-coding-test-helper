"""벡터 색인 시험. 가짜 임베딩(글자 두 개씩 해시)이라 모델도 네트워크도 쓰지 않는다. qdrant-client가 없으면 건너뛴다.
실제 모델 시험(E5Test)은 모델 파일과 onnxruntime·tokenizers가 있을 때만 돈다."""

import importlib.util
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock
import zlib

from ..knowledge import embed as e5
from ..knowledge.index import PATTERN_WEIGHT, ProblemIndex, open_index, overlap

HAS_QDRANT = importlib.util.find_spec("qdrant_client") is not None
# 실제 모델이 놓인 곳: 정해 준 폴더, 없으면 설치 파일을 만들며 받아 둔 폴더(app/packaging/models)
MODEL_DIR = os.environ.get("ALGOBLOCK_EMBED_DIR") or str(Path(__file__).resolve().parents[2] / "packaging" / "models")
HAS_MODEL = e5.present(MODEL_DIR) and all(importlib.util.find_spec(name) for name in ("onnxruntime", "tokenizers", "numpy"))


def fake_embed(dim: int = 32):
    """글자 두 개씩 묶어 해시한 자리에 1을 더한다. 겹치는 글자가 많을수록 가깝다."""

    def embed(texts):
        out = []
        for text in texts:
            vector = [0.0] * dim
            for i in range(len(text) - 1):
                vector[zlib.crc32(text[i : i + 2].encode()) % dim] += 1.0
            out.append(vector)
        return out

    return embed


COUNT = "문자열 배열 두 개. 남는 원소 하나를 구한다. 중복 가능"
STACK = "문자열. 참거짓을 구한다. 가장 나중에 연 것부터 닫는다"
PAIRS = "정수 배열과 정수. 쌍의 개수를 구한다. 두 개를 골라 합을 본다"


@unittest.skipUnless(HAS_QDRANT, "qdrant-client 없음")
class ProblemIndexTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)
        self.index = self.open()

    def open(self, dim: int = 32) -> ProblemIndex:
        index = ProblemIndex(self.dir.name, embed=fake_embed(dim))
        self.addCleanup(index.close)
        return index

    def fill(self):
        self.index.put("p1", COUNT, payload={"title": "남은 한 명", "algorithm": "hash", "patterns": ["dup_names"]})
        self.index.put("p2", STACK, flow="그릇 만들기 / 하나씩 보기 / 짝 맞추기", payload={"title": "문 닫기", "patterns": ["recent_first"]})
        self.index.put("p3", PAIRS, payload={"title": "두 개 고르기", "patterns": ["choose_two_small_n"]})

    def test_empty_index_returns_nothing(self):
        self.assertEqual(self.index.similar(COUNT), [])

    def test_put_then_similar(self):
        self.fill()
        rows = self.index.similar(COUNT + " 길이 100,000 이하", limit=2)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["problem_id"], "p1")
        self.assertGreater(rows[0]["score"], rows[1]["score"])
        self.assertEqual(rows[0]["payload"], {"problem_id": "p1", "title": "남은 한 명", "algorithm": "hash", "patterns": ["dup_names"]})

    def test_flow_vector_is_stored_only_when_given(self):
        self.fill()
        points, _ = self.index.client.scroll("problem", with_vectors=True, limit=10)
        names = {point.payload["problem_id"]: set(point.vector) for point in points}
        self.assertEqual(names, {"p1": {"spec"}, "p2": {"spec", "flow"}, "p3": {"spec"}})

    def test_exclude_drops_the_current_problem(self):
        self.fill()
        self.assertEqual(self.index.similar(COUNT, limit=1)[0]["problem_id"], "p1")
        rows = self.index.similar(COUNT, exclude="p1", limit=5)
        self.assertEqual(sorted(row["problem_id"] for row in rows), ["p2", "p3"])

    def test_delete_drops_one_problem_from_search(self):
        self.index.delete("p1")  # 컬렉션이 없어도 조용히 넘어간다
        self.fill()
        self.index.delete("p1")
        self.index.delete("없는 문항")
        self.assertEqual(sorted(row["problem_id"] for row in self.index.similar(COUNT, limit=5)), ["p2", "p3"])
        self.assertEqual(self.index.count(), 2)

    def test_survives_close_and_reopen(self):
        self.fill()
        self.index.close()
        self.index = self.open()
        self.assertEqual(self.index.similar(STACK, limit=1)[0]["problem_id"], "p2")

    def test_put_again_replaces(self):
        self.fill()
        self.index.put("p1", STACK, payload={"title": "바뀐 글"})
        rows = self.index.similar(STACK, limit=10)
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["problem_id"] for row in rows[:2]}, {"p1", "p2"})
        self.assertEqual(next(row for row in rows if row["problem_id"] == "p1")["payload"], {"problem_id": "p1", "title": "바뀐 글"})

    def test_other_dimension_rebuilds_the_collection(self):
        self.fill()
        self.index.close()
        self.index = self.open(dim=8)  # 모델이 바뀌었다
        self.assertEqual(self.index.similar(COUNT), [])  # 예전 벡터와는 비교할 수 없다. 오류 없이 비운다
        self.index.put("p9", COUNT)
        self.assertEqual([row["problem_id"] for row in self.index.similar(COUNT, limit=5)], ["p9"])

    def test_other_embedder_rebuilds_even_with_the_same_dimension(self):
        """임베딩 이름을 폴더에 적어 둔다. 차원이 같아도 이름이 다르면 견줄 수 없는 벡터라 비운다(섞이면 다른 문항이 불려 온다)."""
        self.fill()
        self.index.close()
        self.assertEqual((Path(self.dir.name) / "embedder.txt").read_text(encoding="utf-8"), "주입")
        self.index = ProblemIndex(self.dir.name, embed=fake_embed(32), name="다른 임베딩")
        self.addCleanup(self.index.close)
        self.assertEqual(self.index.similar(COUNT), [])
        self.index.close()
        self.index = ProblemIndex(self.dir.name, embed=fake_embed(32), name="다른 임베딩")  # 같은 이름으로 다시 열면 그대로 둔다
        self.addCleanup(self.index.close)
        self.index.put("p9", COUNT)
        self.index.close()
        self.index = ProblemIndex(self.dir.name, embed=fake_embed(32), name="다른 임베딩")
        self.addCleanup(self.index.close)
        self.assertEqual([row["problem_id"] for row in self.index.similar(COUNT)], ["p9"])
        self.index.close()
        (Path(self.dir.name) / "embedder.txt").unlink()  # 이름표가 없는 색인(예전 버전이 만든 것)도 비운다
        self.index = ProblemIndex(self.dir.name, embed=fake_embed(32), name="다른 임베딩")
        self.addCleanup(self.index.close)
        self.assertEqual(self.index.similar(COUNT), [])

    def test_threads_can_share_one_index(self):
        """로컬 모드는 스레드에 안전하지 않아 색인이 잠근다. 잠그지 않으면 put이 빠진다."""
        failed = []

        def work(n: int):
            try:
                for i in range(20):
                    self.index.put(f"t{n}-{i}", f"{COUNT} {n} {i}")
                    self.index.similar(COUNT, patterns=["dup_names"])
            except Exception as exc:
                failed.append(exc)

        threads = [threading.Thread(target=work, args=(n,)) for n in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(failed, [])
        self.assertEqual(len(self.index.similar(COUNT, limit=100)), 80)

    def test_pattern_overlap_reorders(self):
        """점수 = 코사인 + PATTERN_WEIGHT × 자카드. 글은 덜 비슷해도 패턴이 같으면 앞에 온다."""
        self.index.put("near", COUNT, payload={"patterns": ["kinds_count"]})
        self.index.put("same_pattern", COUNT + " 길이 100 이하", payload={"patterns": ["dup_names"]})
        plain = self.index.similar(COUNT, limit=2)
        self.assertEqual([row["problem_id"] for row in plain], ["near", "same_pattern"])
        self.assertLess(plain[0]["score"] - plain[1]["score"], PATTERN_WEIGHT)  # 이 차이를 가중치가 뒤집는다
        boosted = self.index.similar(COUNT, limit=2, patterns=["dup_names"])
        self.assertEqual([row["problem_id"] for row in boosted], ["same_pattern", "near"])
        self.assertAlmostEqual(boosted[0]["score"], plain[1]["score"] + PATTERN_WEIGHT * 1.0)
        self.assertAlmostEqual(boosted[1]["score"], plain[0]["score"])

    def test_partial_overlap_gets_part_of_the_weight(self):
        self.index.put("p1", COUNT, payload={"patterns": ["dup_names", "pair_lookup"]})
        plain = self.index.similar(COUNT)[0]["score"]
        self.assertAlmostEqual(self.index.similar(COUNT, patterns=["dup_names"])[0]["score"], plain + PATTERN_WEIGHT / 2)


class OverlapTest(unittest.TestCase):
    def test_jaccard(self):
        self.assertEqual(overlap(["a"], ["a"]), 1.0)
        self.assertEqual(overlap(["a", "b"], ["a"]), 0.5)
        self.assertEqual(overlap(["a"], ["b"]), 0.0)
        self.assertEqual(overlap([], ["a"]), 0.0)
        self.assertEqual(overlap(None, None), 0.0)


class OpenIndexTest(unittest.TestCase):
    def test_none_when_qdrant_is_missing(self):
        with tempfile.TemporaryDirectory() as path:
            had, real = "qdrant_client" in sys.modules, sys.modules.get("qdrant_client")
            with mock.patch("importlib.util.find_spec", return_value=None):
                self.assertIsNone(open_index(path))
            self.assertEqual(("qdrant_client" in sys.modules, sys.modules.get("qdrant_client")), (had, real))

    def test_none_when_the_model_is_missing(self):
        """임베딩은 기기 안 모델 하나뿐이다. 파일이 없으면 다른 임베딩으로 갈아타지 않고 색인을 열지 않는다."""
        with tempfile.TemporaryDirectory() as path, tempfile.TemporaryDirectory() as empty:
            self.assertIsNone(open_index(path, model_dir=empty))
            with mock.patch.dict(os.environ, {"ALGOBLOCK_EMBED_DIR": "", "OPENAI_API_KEY": "sk-test"}):
                self.assertIsNone(open_index(path))  # 키가 있어도 바깥 임베딩을 쓰지 않는다
            self.assertFalse(os.listdir(path))  # 색인 폴더에 아무것도 만들지 않았다

    def test_chargram_baseline_is_deterministic(self):
        from ..knowledge.index import chargram_embedder

        same, other = chargram_embedder()(["정수 배열, 남는 원소 하나", "정수 배열, 남는 원소 하나"]), chargram_embedder()(["문자열 뒤집기"])
        self.assertEqual(same[0], same[1])
        self.assertNotEqual(same[0], other[0])

    def test_openai_embedding_request_shape(self):
        from ..llm.client import _backend_session

        _backend_session()
        from app.llm.openai.api_key.embed import embed
        from app.llm.wire import set_transport

        seen = {}

        def transport(url, headers, body, timeout):
            seen.update(url=url, auth=headers["Authorization"], body=body)
            return {"data": [{"index": 1, "embedding": [0.2]}, {"index": 0, "embedding": [0.1]}]}

        set_transport(transport)
        try:
            with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                self.assertEqual(embed(["가", "나"]), [[0.1], [0.2]])  # index 순서로
        finally:
            set_transport(None)
        self.assertEqual((seen["url"], seen["auth"]), ("https://api.openai.com/v1/embeddings", "Bearer sk-test"))
        self.assertEqual(seen["body"], {"model": "text-embedding-3-small", "input": ["가", "나"]})


@unittest.skipUnless(HAS_MODEL, "임베딩 모델 파일이나 onnxruntime·tokenizers 없음")
class E5Test(unittest.TestCase):
    def test_real_model_vectors(self):
        """384차원, 길이 1, 같은 글은 같은 벡터. 말씨가 달라도 같은 구조가 다른 구조보다 가깝다.
        (영어 명세는 패턴 겹침 없이 이 모델만으로는 모자라서 여기서 견주지 않는다.)"""
        embed = e5.e5_embedder(MODEL_DIR)
        base = "문자열 배열 두 개가 주어진다. 첫 번째 배열에는 있지만 두 번째 배열에서 빠진 원소 하나를 찾는다."
        para = "배열 둘이 입력으로 들어온다. 앞 배열에만 남는 문자열 하나를 돌려준다."
        other = "정수 배열에서 잇달아 나오는 같은 값을 하나로 줄인다."
        a, a2, b, d = embed([base, base, para, other])
        self.assertEqual((len(a), a), (e5.DIM, a2))
        self.assertAlmostEqual(sum(x * x for x in a), 1.0, places=4)
        cosine = lambda x, y: sum(i * j for i, j in zip(x, y))  # noqa: E731
        self.assertGreater(cosine(a, b), cosine(a, d))

    @unittest.skipUnless(HAS_QDRANT, "qdrant-client 없음")
    def test_open_index_uses_the_one_model(self):
        with tempfile.TemporaryDirectory() as path:
            index = open_index(path, model_dir=MODEL_DIR)
            try:
                self.assertEqual(index.model, e5.NAME)
                index.put("p1", COUNT)
                index.put("p2", PAIRS)
                self.assertEqual(index.similar(COUNT + " 길이 100 이하", limit=1)[0]["problem_id"], "p1")
            finally:
                index.close()
            self.assertEqual((Path(path) / "embedder.txt").read_text(encoding="utf-8"), e5.NAME)
