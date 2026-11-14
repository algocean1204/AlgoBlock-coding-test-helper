"""비슷한 문항 찾기의 어려운 측정: 명세의 말씨와 틀이 달라져도(형식이 깨져도) 같은 구조를 찾는가.

app에서:
  python3 -m tutor.eval.recall_hard variants            # 바꿔 쓴 명세를 만든다(모델을 부른다. 한 번만, results/recall-hard.json)
  python3 -m tutor.eval.recall_hard run --model NAME    # 모델 하나를 잰다(char-3gram 또는 fastembed 모델 이름)

recall_bench의 함정 문항 20개(구조 8 × 이야기 6)를 그대로 쓴다. 색인에는 원래 명세가 있고, 질의만 바꾼다.
- same     : 원래 명세 → 원래 명세(쉬운 기준. recall_bench의 B팔)
- para     : 다른 낱말과 다른 문장 순서로 바꿔 쓴 명세
- terse    : 명사형 한 줄로 줄인 명세
- other    : 다른 공급자 모델이 실제 프롬프트로 뽑은 명세(공급자를 바꾼 사용자)
- english  : 영어로 쓴 명세(가장 크게 깨진 경우)
- leak     : 이야기 낱말이 남은 명세끼리(추상화가 덜 된 경우. 같은 이야기의 함정이 세진다)
- pool57   : 바꿔 쓴 질의로, 다른 문항의 원래·한 줄·이야기 남은 명세 57개에서 찾기(후보가 많고 함정이 여럿)
점수는 코사인만(w=0)과 코사인 + 0.3×패턴 겹침 둘 다 낸다. 후보에서 질의와 같은 문항은 늘 뺀다.
"""

import argparse
import json
import os
import resource
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context

from ..knowledge.index import PATTERN_WEIGHT, chargram_embedder, overlap
from ..knowledge.ontology import known_patterns
from ..llm import llm
from ..plan.prompts import abstract_text
from ..state import Abstract
from .recall_bench import BY_ID, CHARGRAM, PROBLEMS, SPECS

HARD = SPECS.with_name("recall-hard.json")
OTHER_MODEL = os.environ.get("ALGOBLOCK_HARD_OTHER", "openai/gpt-6-luna")
REWRITE = {
    "para": "아래 문제 명세를 뜻은 그대로 두고 다른 낱말과 다른 문장 순서로 다시 써라. 원문의 표현을 되도록 쓰지 말고 비슷한말로 바꾼다. 숫자와 조건은 빠뜨리지 않는다. 다시 쓴 명세만 출력한다.",
    "terse": "아래 문제 명세를 명사형으로 끝나는 한 줄(60자 안팎)로 줄여라. 입력의 꼴과 구해야 하는 것만 남긴다. 줄인 한 줄만 출력한다.",
    "english": "Rewrite the following problem specification in plain English. Keep every number and condition. Output only the rewritten specification.",
    "leak": "아래는 문제 글과 그 명세다. 명세를 다시 쓰되, 문제 글에 나오는 이야기 낱말(장소, 사물, 사람)을 그대로 살려서 쓴다. 변수 이름은 쓰지 않는다. 두세 문장. 다시 쓴 명세만 출력한다.",
}
CONDITIONS = ("same", "para", "terse", "other", "english", "leak", "pool57")


def make_variants() -> None:
    specs = json.loads(SPECS.read_text(encoding="utf-8"))
    hard = json.loads(HARD.read_text(encoding="utf-8")) if HARD.exists() else {}

    def one(p):
        row, base = hard.get(p["id"], {}), specs[p["id"]]["spec"]
        for name, order in REWRITE.items():
            if name not in row:
                body = f"문제 글:\n{p['text']}\n\n명세:\n{base}" if name == "leak" else base
                row[name] = llm().use([{"role": "user", "content": f"{order}\n\n{body}"}], None, task="eval.rewrite").strip()
        if "other" not in row:
            try:
                got: Abstract = llm(OTHER_MODEL).use(abstract_text(p["text"]), Abstract, task="plan.abstract")
                row["other"], row["other_patterns"] = got.spec.strip(), known_patterns(got.patterns)
            except Exception as exc:  # noqa: BLE001 - 다른 공급자가 안 되면 그 조건만 뺀다
                row["other_error"] = f"{type(exc).__name__}: {exc}"[:200]
        return p["id"], row

    contexts = [copy_context() for _ in PROBLEMS]
    with ThreadPoolExecutor(max_workers=4) as pool:
        hard.update(dict(pool.map(lambda pair: pair[0].run(one, pair[1]), zip(contexts, PROBLEMS))))
    HARD.parent.mkdir(exist_ok=True)
    HARD.write_text(json.dumps(hard, ensure_ascii=False, indent=1), encoding="utf-8")
    done = {name: sum(name in row for row in hard.values()) for name in (*REWRITE, "other")}
    print("만든 수:", done, "| other 실패:", next((row["other_error"] for row in hard.values() if "other_error" in row), "없음"))


def embedder(model: str):
    if model == CHARGRAM:
        return chargram_embedder()
    if model == "app":  # 앱이 실제로 쓰는 길(onnxruntime 직접). ALGOBLOCK_EMBED_DIR의 model.onnx를 그대로 잰다
        from ..knowledge.embed import e5_embedder

        return e5_embedder(os.environ["ALGOBLOCK_EMBED_DIR"])
    from fastembed import TextEmbedding

    if "e5-small" in model:  # fastembed 목록에 없는 작은 e5. 허깅페이스의 ONNX 파일을 그대로 쓴다
        from fastembed.common.model_description import ModelSource, PoolingType

        TextEmbedding.add_custom_model(model=model, pooling=PoolingType.MEAN, normalization=True, sources=ModelSource(hf=model), dim=384, model_file=os.environ.get("ALGOBLOCK_HARD_E5_FILE", "onnx/model.onnx"))  # model_O4.onnx(반정밀), model_qint8_avx512_vnni.onnx(8비트)도 잴 수 있다
    loaded = TextEmbedding(model, cache_dir=os.environ.get("FASTEMBED_CACHE_PATH"))
    prefix = "query: " if "e5" in model else ""  # e5 계열은 양쪽 모두에 붙인다(대칭 비교)
    return lambda texts: [vector.tolist() for vector in loaded.embed([prefix + text for text in texts])]


def cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / ((sum(x * x for x in a) ** 0.5) * (sum(y * y for y in b) ** 0.5) or 1.0)


def run(model: str) -> None:
    specs = json.loads(SPECS.read_text(encoding="utf-8"))
    hard = json.loads(HARD.read_text(encoding="utf-8"))
    began = time.perf_counter()
    embed = embedder(model)
    embed(["처음 올리기"])
    load = time.perf_counter() - began

    text = {("same", p["id"]): specs[p["id"]]["spec"] for p in PROBLEMS}
    for p in PROBLEMS:
        for name in (*REWRITE, "other"):
            if name in hard[p["id"]]:
                text[(name, p["id"])] = hard[p["id"]][name]
    keys = list(text)
    laps = []
    vectors = {}
    for key in keys:  # 하나씩 넣어 실제 쓰임(문항 하나 저장, 질의 하나)의 시간을 잰다
        began = time.perf_counter()
        vectors[key] = embed([text[key]])[0]
        laps.append(time.perf_counter() - began)
    patterns = {p["id"]: specs[p["id"]]["patterns"] for p in PROBLEMS}

    def score(query_kind: str, pool_kinds: tuple[str, ...], weight: float) -> tuple[float, float, float, int]:
        p1 = rr = trap = n = 0
        for q in PROBLEMS:
            if (query_kind, q["id"]) not in vectors:
                continue
            query_patterns = hard[q["id"]].get("other_patterns", patterns[q["id"]]) if query_kind == "other" else patterns[q["id"]]
            rows = []
            for kind in pool_kinds:
                for o in PROBLEMS:
                    if o is q or (kind, o["id"]) not in vectors:
                        continue
                    rows.append((cosine(vectors[(query_kind, q["id"])], vectors[(kind, o["id"])]) + weight * overlap(query_patterns, patterns[o["id"]]), o["id"]))
            order = [BY_ID[pid] for _, pid in sorted(rows, key=lambda row: (-row[0], row[1]))]
            p1 += order[0]["group"] == q["group"]
            trap += order[0]["story"] == q["story"]
            rr += 1 / next(i for i, other in enumerate(order, 1) if other["group"] == q["group"])
            n += 1
        return (p1 / n, rr / n, trap / n, n) if n else (0.0, 0.0, 0.0, 0)

    plans = {"same": ("same", ("same",)), "para": ("para", ("same",)), "terse": ("terse", ("same",)), "other": ("other", ("same",)),
             "english": ("english", ("same",)), "leak": ("leak", ("leak",)), "pool57": ("para", ("same", "terse", "leak"))}
    result = {"model": model, "dim": len(vectors[keys[0]]), "load_s": round(load, 2), "embed_ms": round(statistics.median(laps) * 1000, 1),
              "embed_max_ms": round(max(laps) * 1000, 1), "rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1e6 if sys.platform == "darwin" else 1e3)), "rows": {}}
    for name in CONDITIONS:
        query_kind, pool_kinds = plans[name]
        result["rows"][name] = {"plain": score(query_kind, pool_kinds, 0.0), "pattern": score(query_kind, pool_kinds, PATTERN_WEIGHT)}
    print(json.dumps(result, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("what", choices=("variants", "run"))
    parser.add_argument("--model", default=CHARGRAM)
    args = parser.parse_args()
    make_variants() if args.what == "variants" else run(args.model)


if __name__ == "__main__":
    main()
