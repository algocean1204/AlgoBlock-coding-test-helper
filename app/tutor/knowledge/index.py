"""비슷한 문항 찾기(벡터). 문항마다 점 하나, 이름 붙은 벡터 둘: spec(뼈대 명세), flow(풀이 흐름).

Qdrant 로컬 모드(서버 없음, 폴더 하나)를 쓴다. 처음 쓸 때 import한다(없어도 이 모듈은 import된다).
임베딩은 하나뿐이다: 기기 안 모델 multilingual-e5-small(knowledge/embed.py). 키나 네트워크에 따라 바뀌지 않는다.
모델을 올릴 수 없으면(파일이나 패키지가 없으면) 다른 임베딩으로 갈아타지 않고 색인을 열지 않는다(open_index가 None).
형식이 다른 벡터가 섞이면 같은 질문에 다른 문항이 불려 오기 때문이다. 그때는 온톨로지와 SQLite만으로 돈다.
이 색인은 캐시다. 원본은 store에 있다. 색인 폴더의 embedder.txt에 임베딩 이름을 적어 두고, 지금 것과 다르면 컬렉션을 비운다.
비운 색인은 부르는 쪽(Tutor.reindex)이 SQLite의 명세로 다시 채운다. 사용자가 할 일은 없다.
로컬 모드는 폴더를 프로세스 하나만 연다(둘째는 RuntimeError).

점수 = spec 코사인 유사도 + PATTERN_WEIGHT × 패턴 자카드(겹친 수 ÷ 합친 수). patterns를 안 주면 코사인만 본다.
eval/recall_bench.py(쉬운 기준)와 eval/recall_hard.py(바꿔 쓴 명세, 다른 공급자, 영어, 이야기 낱말이 남은 명세)로 쟀다.
가중치는 0.3이다(eval/recall_bench.py로 고른다). 0.15는 임베딩 모델에 따라 모자랐고 0.3부터는 어느 모델이든 같은 구조를 1등으로 올린다.
"""

import importlib.util
import os
import shutil
import threading
import uuid
import zlib
from pathlib import Path

from . import embed as e5

COLLECTION = "problem"
PATTERN_WEIGHT = 0.3
CANDIDATES = 200  # 한계: 패턴으로 다시 줄 세우는 후보 수. 문항이 이보다 많아지면 패턴 필터 질의를 하나 더 합친다


def chargram_embedder(dim: int = 2048):
    """모델 없는 임베딩: 글자 세 개씩 해시해 센 벡터. 앱은 쓰지 않는다. 시험과 측정의 기준선으로만 둔다.

    같은 틀로 쓴 명세에서는 모델과 비슷하지만 말씨가 바뀌면 떨어지고 영어 명세에서는 무너진다.
    """

    def embed(texts: list[str]) -> list[list[float]]:
        out = []
        for text in texts:
            vector = [0.0] * dim
            for i in range(len(text) - 2):
                vector[zlib.crc32(text[i : i + 3].encode()) % dim] += 1.0
            out.append(vector)
        return out

    return embed


def point_id(problem_id: str) -> str:
    """문항 id에서 정해지는 점 id(같은 문항은 같은 점)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, problem_id))


def overlap(a, b) -> float:
    """패턴 자카드. 한쪽이 비면 0."""
    a, b = set(a or []), set(b or [])
    return len(a & b) / len(a | b) if a and b else 0.0


class ProblemIndex:
    def __init__(self, path: str, embed=None, name: str = "주입", model_dir: str | None = None):
        """embed를 주면 그 임베딩을 쓴다(시험·측정. name으로 구분한다). 안 주면 model_dir의 기기 안 모델."""
        self.path, self.client = Path(path), None
        self.model, self.embed = (name, embed) if embed else (e5.NAME, e5.e5_embedder(model_dir))
        self.weight = PATTERN_WEIGHT
        self.lock = threading.Lock()  # 로컬 모드는 여러 스레드가 함께 쓰면 깨진다(여러 스레드가 함께 쓰면 put이 InterfaceError로 빠진다)
        marker = self.path / "embedder.txt"
        made_by = marker.read_text(encoding="utf-8").strip() if marker.is_file() else ""  # 이름표가 없으면 예전 버전이 만든 색인이다
        self._open(wipe=made_by != self.model)  # 다른 임베딩으로 만든 벡터는 비운다(차원이 같아도 견줄 수 없다)
        marker.write_text(self.model, encoding="utf-8")

    def _open(self, wipe: bool = False) -> None:
        """로컬 Qdrant를 연다. wipe면 색인을 통째로 비우고 연다(이 색인은 캐시다).
        비울 때는 클라이언트를 먼저 닫고 Qdrant의 파일(collection/, meta.json)을 지운다. delete_collection은 열린 저장 파일을 닫지 않은 채 지우려 해서
        Windows에서는 지우지 못하고(조용히 넘어간다) 옛 벡터가 남아 다음 컬렉션에 섞였다."""
        from qdrant_client import QdrantClient

        if self.client is not None:
            self.client.close()
            self.client = None
        if wipe:
            if (self.path / "collection").is_dir():
                shutil.rmtree(self.path / "collection")  # 닫은 뒤라 지워진다. 못 지우면 옛 벡터가 섞이므로 넘기지 않고 오류를 낸다
            (self.path / "meta.json").unlink(missing_ok=True)
        self.client = QdrantClient(path=str(self.path))

    def clear(self) -> None:
        """색인을 통째로 비운다(모델이 바뀌었을 때처럼. 부르는 쪽이 원본에서 다시 채운다)."""
        with self.lock:
            self._open(wipe=True)

    def _ensure(self, size: int) -> None:
        """컬렉션이 없으면 만들고, 저장된 차원이 지금 모델과 다르면 지우고 다시 만든다."""
        from qdrant_client import models

        if self.client.collection_exists(COLLECTION):
            if self.client.get_collection(COLLECTION).config.params.vectors["spec"].size == size:
                return
            self._open(wipe=True)  # 차원이 다른 옛 벡터(부르는 쪽이 이미 lock을 쥐고 있다)
        params = models.VectorParams(size=size, distance=models.Distance.COSINE)
        self.client.create_collection(COLLECTION, vectors_config={"spec": params, "flow": params})

    def put(self, problem_id: str, spec: str, flow: str = "", payload: dict | None = None) -> None:
        """넣거나 바꾼다. 점 id는 problem_id에서 정해져 같은 문항은 같은 점이다. flow가 비면 spec 벡터만 둔다."""
        from qdrant_client import models

        vectors = dict(zip(("spec", "flow"), self.embed([spec, flow] if flow else [spec])))
        point = models.PointStruct(id=point_id(problem_id), vector=vectors,
                                   payload={**(payload or {}), "problem_id": problem_id})
        with self.lock:
            self._ensure(len(vectors["spec"]))
            self.client.upsert(COLLECTION, points=[point])

    def delete(self, problem_id: str) -> None:
        """문항 하나를 뺀다(문항을 지우거나 글을 고쳤을 때). 컬렉션이나 그 문항이 없으면 조용히 넘어간다."""
        from qdrant_client import models

        with self.lock:
            if self.client.collection_exists(COLLECTION):
                self.client.delete(COLLECTION, points_selector=models.PointIdsList(points=[point_id(problem_id)]))

    def similar(self, spec: str, exclude: str | None = None, limit: int = 3, patterns: list[str] | None = None) -> list[dict]:
        """[{"problem_id", "score", "payload"}], 점수 높은 순. exclude는 지금 문항. patterns를 주면 패턴 겹침을 더해 다시 줄 세운다."""
        from qdrant_client import models

        vector = self.embed([spec])[0]
        skip = None
        if exclude:
            skip = models.Filter(must_not=[models.FieldCondition(key="problem_id", match=models.MatchValue(value=exclude))])
        with self.lock:
            self._ensure(len(vector))
            hits = self.client.query_points(COLLECTION, query=vector, using="spec", query_filter=skip, with_payload=True,
                                            limit=max(limit, CANDIDATES) if patterns else limit).points
        rows = [{"problem_id": hit.payload["problem_id"], "payload": hit.payload,
                 "score": hit.score + self.weight * overlap(patterns, hit.payload.get("patterns"))} for hit in hits]
        rows.sort(key=lambda row: -row["score"])
        return rows[:limit]

    def count(self) -> int:
        with self.lock:
            return self.client.count(COLLECTION).count if self.client.collection_exists(COLLECTION) else 0

    def close(self) -> None:
        with self.lock:
            self.client.close()


def open_index(path: str, model_dir: str | None = None) -> "ProblemIndex | None":
    """색인을 연다. 모델 폴더는 model_dir, 없으면 환경 변수 ALGOBLOCK_EMBED_DIR.

    qdrant-client·onnxruntime·tokenizers 가운데 하나라도 없거나 모델 파일이 없으면 None이다(비슷한 문항 찾기를 끄고 온톨로지·SQLite만으로 돈다).
    """
    directory = model_dir or os.environ.get("ALGOBLOCK_EMBED_DIR", "")
    if any(importlib.util.find_spec(name) is None for name in ("qdrant_client", "onnxruntime", "tokenizers")):
        return None
    if not directory or not e5.present(directory):
        return None
    try:
        return ProblemIndex(path, model_dir=directory)
    except ImportError:
        return None
