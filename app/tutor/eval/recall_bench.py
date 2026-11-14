"""비슷한 문항 찾기 측정. 이야기와 구조가 어긋나게 이 프로젝트에서 새로 쓴 함정 문항 20개로 잰다.

app에서:
  python3 -m tutor.eval.recall_bench [--cli] [--model NAME ...] [--detail]
--cli 는 뼈대(spec, patterns)를 이 PC의 Claude Code(claude -p, haiku)로 뽑는다. 문항마다 한 번만 뽑아 results/recall-specs.json에 두고 다시 쓴다.
--model 은 fastembed 임베딩 모델 이름(여러 번 줄 수 있다). 빼면 MODELS 전부. char-3gram은 모델 없는 기준선이다.

함정 세트: 구조(group) 8개 × 이야기(story) 6개. 같은 구조는 이야기가 다르고, 같은 이야기는 구조가 다르다.
같은 구조끼리는 글투(함수형·입출력형·서술형)와 제한 숫자도 다르게 썼다. 같은 구조의 제한사항 문장이 비슷하면
글자 겹침만으로 문제 글에서 구조가 맞아 버리기 때문이다.
mask_tail, repeat_rule은 온톨로지에 맞는 패턴이 없는 구조다(패턴만으로는 못 찾는 경우).
질의 하나마다 나머지 19개를 줄 세운다. P@1 = 1등이 같은 구조, MRR = 같은 구조가 처음 나오는 자리의 역수, 함정 = 1등이 같은 이야기(다른 구조).
팔: A 문제 글 그대로 / B 뼈대 명세 / C 명세 + 패턴 겹침(색인의 점수식) / D 패턴 겹침만(벡터 없음) / R 무작위.
동점은 무작위로 가르고 SHUFFLES번 평균한다(D와 R만 해당).
가중치는 개발 절반(DEV)의 질의로만 정한다: P@1, MRR이 가장 좋은 값들 가운데 가운데 값. 보류 절반은 표에서 따로 본다.
"""

import argparse
import json
import os
import random
import statistics
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from contextvars import copy_context
from pathlib import Path

from ..knowledge import index as knowledge_index
from ..knowledge.index import ProblemIndex, chargram_embedder, overlap
from ..knowledge.ontology import known_patterns
from ..llm import llm, use_llm
from ..plan.prompts import abstract_text
from ..state import Abstract
from .cli_client import ClaudeCli

RESULTS = Path(__file__).resolve().parent / "results"
SPECS = RESULTS / "recall-specs.json"

DEV = ("leftover_one", "adjacent_dedupe", "flip_fit", "mask_tail")  # 나머지 넷(recent_match, pair_sum, kinds_cap, repeat_rule)이 보류
OPENAI = "openai/text-embedding-3-small"  # --model 로 줄 때만 돈다(키와 요금이 든다)
CHARGRAM = "char-3gram"  # 모델 없는 기준선: 글자 세 개씩 해시해 센 벡터. 명세의 낱말 겹침만으로 어디까지 되는지 본다
MODELS = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "minishlab/potion-multilingual-128M",
    CHARGRAM,
]
GRID = (0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0)
SHUFFLES = 200


def P(pid: str, group: str, story: str, text: str) -> dict:
    return {"id": pid, "group": group, "story": story, "text": text.strip()}


PROBLEMS = [
    # ── 개발 절반: 이야기 마라톤·도서관·주차장 ──
    P("marathon_leftover", "leftover_one", "마라톤", """
마라톤 대회의 물품 보관소는 선수가 맡긴 가방마다 선수가 속한 클럽의 이름표를 붙입니다. 출발 전에 맡긴 가방의 이름표를 적은 배열 dropped와 경기가 끝난 뒤 찾아간 가방의 이름표를 적은 배열 collected가 주어집니다.
보관소를 닫을 때 가방이 딱 하나 남아 있었습니다. 남은 가방의 이름표를 return 하도록 solution 함수를 완성하세요.
제한사항
- dropped의 길이는 2 이상 80,000 이하이고, collected의 길이는 dropped보다 1 작습니다.
- 이름표는 알파벳 대문자 2~12자입니다.
- 한 클럽에서 여러 선수가 나오므로 같은 이름표가 여러 번 적힐 수 있습니다."""),
    P("library_leftover", "leftover_one", "도서관", """
어느 도서관에서 하루 동안 빌려 간 책의 제목 목록과 돌려받은 책의 제목 목록을 적어 두었다. 문을 닫을 때 보니 빌려 간 책 가운데 꼭 한 권이 돌아오지 않았다. 돌아오지 않은 책의 제목을 구하라.
입력: 빌려 간 책 제목의 문자열 배열 borrowed(책 2권 이상 200,000권 이하), 돌려받은 책 제목의 문자열 배열 returned(borrowed보다 한 권 적다). 제목은 영어 소문자로 30자를 넘지 않는다.
출력: 돌아오지 않은 책의 제목.
참고: 같은 제목의 책을 여러 권 갖추고 있어서 한 제목이 여러 번 적힐 수 있다."""),
    P("parking_leftover", "leftover_one", "주차장", """
주차장 관리인이 들어온 차와 나간 차의 번호판 뒤 네 자리를 각각 entered, exited라는 문자열 배열에 받아 적었어요. 하루에 들어오는 차는 많아야 5만 대이고, 뒤 네 자리가 똑같은 차가 여러 대일 수도 있어요.
영업을 마치고 보니 주차장에 차가 딱 한 대 남아 있었습니다. exited에는 그 차만 빠져 있어요.
남아 있는 차의 번호 네 자리를 구해 주세요."""),
    P("marathon_dedupe", "adjacent_dedupe", "마라톤", """
마라톤 코스는 1번부터 42번까지 1킬로미터마다 번호가 붙은 구간으로 나뉜다. 선수의 손목 센서는 선수가 한 구간에 머무는 동안 그 구간 번호를 여러 번 잇달아 기록한다. 잇달아 기록된 같은 번호를 하나로 줄여, 선수가 지나간 구간을 차례대로 구하라.
입력: 센서 기록을 담은 정수 배열 log(길이 1 이상 400,000 이하).
출력: 지나간 구간 번호를 차례대로 담은 배열.
참고: 왕복 코스라서 지나갔던 구간을 나중에 또 지날 수 있고, 그때는 다시 넣는다. [7, 7, 8, 8, 8, 7, 7]이면 [7, 8, 7]이다."""),
    P("library_dedupe", "adjacent_dedupe", "도서관", """
도서관 사서가 반납함에서 책을 한 권씩 꺼내며 분류 번호(1부터 100까지의 정수)를 꺼낸 순서대로 배열 codes에 적었어요. 책은 많으면 50만 권까지 나와요.
사서는 분류 번호가 같은 책이 바로 이어서 나오면 한 묶음으로 묶습니다. 번호가 같더라도 중간에 다른 번호의 책이 끼어 있었다면 다른 묶음이에요. 예를 들어 [4, 4, 4, 3, 3, 4]는 세 묶음이 됩니다.
묶음마다 분류 번호를 하나씩, 묶인 순서대로 늘어놓은 배열을 구해 주세요."""),
    P("parking_dedupe", "adjacent_dedupe", "주차장", """
주차장 입구 카메라가 인식한 차량 번호가 인식한 순서대로 담긴 배열 seen이 주어집니다. 카메라는 차 한 대가 지나가는 동안 같은 번호를 여러 번 연속으로 인식합니다.
연속으로 인식된 같은 번호는 차 한 대로 보고, 들어온 차량 번호를 순서대로 담은 배열을 return 하도록 solution 함수를 완성하세요.
제한사항
- seen의 길이는 1 이상 300,000 이하입니다.
- 차량 번호는 1000 이상 9999 이하의 정수입니다.
- 나갔던 차가 다시 들어올 수 있고, 이때는 다시 담습니다. 예: [1234, 1234, 5678, 1234] → [1234, 5678, 1234]"""),
    P("marathon_flip", "flip_fit", "마라톤", """
마라톤 대회 사진팀은 완주한 선수마다 결승선 사진을 뽑아 액자에 넣어 줘요. 사진은 찍은 카메라에 따라 크기가 제각각이고, 사진의 [가로, 세로] 길이를 모아 둔 2차원 배열 photos가 있어요. 사진은 많아야 3,000장, 각 길이는 5부터 800 사이의 자연수예요.
액자는 한 가지 크기로만 맞추려고 합니다. 사진은 돌려서 넣어도 괜찮고, 사진보다 큰 액자에는 여백을 둡니다.
모든 사진이 들어가는 액자 가운데 둘레가 가장 짧은 액자의 둘레를 구해 주세요."""),
    P("parking_flip", "flip_fit", "주차장", """
주차장에 들어오는 차량은 폭과 길이가 저마다 다르다. 어떤 차량이든 세울 수 있도록 주차 칸을 한 가지 크기의 직사각형으로 그리려고 한다. 차량은 방향을 90도 돌려서 세워도 된다. 주차 칸 하나의 넓이를 가장 작게 할 때 그 값을 구하라.
입력: 차량의 [폭, 길이]를 담은 2차원 배열 cars(차량 1대 이상 5,000대 이하, 폭과 길이는 1 이상 500 이하의 자연수).
출력: 주차 칸 넓이의 최솟값."""),
    P("library_mask", "mask_tail", "도서관", """
도서관 대출 영수증에는 회원증 번호를 그대로 찍지 않는다. 회원증 번호는 숫자와 붙임표(-)로 이루어지는데, 끝에서부터 숫자 세 개만 남기고 그 앞의 숫자는 모두 'x'로 바꿔 찍는다. 붙임표는 그 자리에 그대로 둔다. 영수증에 찍히는 문자열을 구하라.
입력: 회원증 번호 문자열 card(길이 5 이상 18 이하, 숫자가 세 개 이상 들어 있다).
출력: 영수증에 찍히는 문자열. card가 "12-3456-78"이면 "xx-xxx6-78"이다."""),
    P("parking_mask", "mask_tail", "주차장", """
주차장에서는 방문 차량 운전자의 연락처를 주차 확인증에 적어 둬요. 다만 다른 사람이 볼 수 있으니 끝의 세 자리만 보이게 하고, 나머지 앞자리는 전부 '#' 기호로 가립니다.
연락처는 숫자로만 된 문자열 phone이고 짧으면 6자, 길면 13자예요. "0312345678"이라면 "#######678"이 됩니다.
확인증에 적힐 문자열을 구해 주세요."""),
    # ── 보류 절반: 이야기 우주선·빵집·놀이공원 ──
    P("spaceship_recent", "recent_match", "우주선", """
우주선 안쪽 구역으로 들어가려면 격벽 문을 차례로 열어야 하고, 나올 때는 가장 나중에 연 문부터 닫아야 합니다. 문 조작 기록이 문자열 log로 주어집니다. 대문자는 그 종류의 문을 연 것이고, 같은 알파벳의 소문자는 그 종류의 문을 닫은 것입니다.
기록이 규칙에 맞고 마지막에 모든 문이 닫혀 있으면 true, 아니면 false를 return 하도록 solution 함수를 완성하세요.
제한사항
- log의 길이는 2 이상 60,000 이하입니다.
- log는 알파벳 A, B, C와 a, b, c로만 이루어져 있습니다.
- 예: "ABbaCc" → true, "ABab" → false, "AB" → false"""),
    P("bakery_recent", "recent_match", "빵집", """
빵집의 식힘 선반에는 빵 판을 한 장씩 위로 포개어 올리고, 내릴 때는 맨 위에 놓인 판만 내릴 수 있다. 하루의 작업 기록이 이 규칙대로 할 수 있는 것이었고 일을 마쳤을 때 선반이 비어 있는지 판별하라.
입력: 작업 기록을 담은 정수 배열 moves(길이 1 이상 200,000 이하). 양수 x는 x번 판을 올린 것, 음수 -x는 x번 판을 내린 것이다(1 ≤ x ≤ 1,000). 번호가 같은 판이 여러 장 있을 수 있다.
출력: 가능한 기록이고 선반이 비었으면 true, 아니면 false. [3, 5, -5, -3]은 true, [3, 5, -3, -5]는 false이다."""),
    P("park_recent", "recent_match", "놀이공원", """
놀이공원 범퍼카 차고는 입구가 하나뿐인 좁은 통로예요. 그래서 맨 마지막에 넣은 차만 뺄 수 있어요.
직원이 하루 동안 차를 넣고 뺀 일을 문자열 배열 records에 적었습니다. "in red"는 빨간 차를 넣었다는 뜻이고 "out red"는 빨간 차를 뺐다는 뜻이에요. 색 이름은 영어 소문자이고, 기록은 5만 줄을 넘지 않으며, 같은 색 차가 여러 대 있을 수 있어요.
적힌 기록이 실제로 가능한 순서이고 하루가 끝났을 때 차고가 비어 있었는지 참/거짓으로 알려 주세요. 예: ["in red", "in blue", "out red"]는 거짓입니다."""),
    P("spaceship_pairs", "pair_sum", "우주선", """
우주선의 보조 화물칸에는 화물 상자를 정확히 두 개 실어야 하고, 두 상자의 무게를 더한 값이 정해진 값 target과 꼭 같아야 균형이 맞는다. 조건에 맞게 상자 두 개를 고르는 방법이 몇 가지인지 구하라.
입력: 상자 무게를 담은 정수 배열 boxes(상자 2개 이상 1,000개 이하, 무게 1 이상 10,000 이하)와 정수 target(2 이상 20,000 이하).
출력: 고르는 방법의 수.
참고: 무게가 같은 상자가 여럿 있을 수 있으며 서로 다른 상자로 센다."""),
    P("bakery_pairs", "pair_sum", "빵집", """
빵집 상품권은 거스름돈을 주지 않아요. 그래서 서로 다른 빵 두 개를 골랐을 때 값의 합이 상품권 금액 coupon과 딱 맞아야만 쓸 수 있습니다.
진열대에 놓인 빵의 가격이 정수 배열 prices에 들어 있어요. 빵은 많아야 500개이고 가격은 100원부터 9,000원 사이예요. 가격이 같은 빵이 여러 개 있어도 서로 다른 빵으로 봅니다.
상품권을 쓸 수 있게 빵 두 개를 고르는 경우가 모두 몇 가지인지 구해 주세요."""),
    P("park_pairs", "pair_sum", "놀이공원", """
놀이공원의 2인용 그네는 탄 두 사람의 몸무게 합이 정확히 balance일 때만 움직입니다. 줄을 선 사람들의 몸무게가 담긴 정수 배열 weights와 정수 balance가 주어집니다.
그네를 움직일 수 있게 두 사람을 고르는 경우의 수를 return 하도록 solution 함수를 완성하세요.
제한사항
- weights의 길이는 2 이상 800 이하입니다.
- 몸무게는 20 이상 150 이하이고, balance는 40 이상 300 이하입니다.
- 몸무게가 같은 사람이 여러 명 있을 수 있고, 서로 다른 사람으로 셉니다."""),
    P("spaceship_kinds", "kinds_cap", "우주선", """
우주선 탐사대가 낯선 행성에서 광물 표본을 모았어요. 표본마다 종류 번호가 있고, 그 번호들이 정수 배열 samples에 들어 있습니다. 표본은 많아야 3만 개, 종류 번호는 1부터 9만 사이예요. 같은 종류의 표본이 여러 개일 수 있어요.
우주선의 표본 칸은 slots개뿐이라 표본을 정확히 slots개만 실을 수 있습니다(slots는 표본 수 이하). 탐사대는 되도록 여러 종류를 가져가고 싶어 해요.
가져갈 수 있는 표본의 종류가 가장 많을 때 몇 종류인지 구해 주세요."""),
    P("bakery_kinds", "kinds_cap", "빵집", """
빵집에서 오늘 구운 빵의 종류 번호가 담긴 정수 배열 breads와 시식 상자 하나에 담을 빵의 개수 box가 주어집니다. 시식 상자에는 빵을 정확히 box개 담습니다.
손님이 되도록 여러 종류를 맛볼 수 있게 담으려고 합니다. 상자에 담을 수 있는 빵 종류 수의 최댓값을 return 하도록 solution 함수를 완성하세요.
제한사항
- breads의 길이는 1 이상 7,000 이하입니다.
- box는 1 이상 breads의 길이 이하입니다.
- 종류 번호는 1 이상 30,000 이하의 자연수입니다.
- 종류가 같은 빵이 여러 개 있을 수 있습니다."""),
    P("park_rule", "repeat_rule", "놀이공원", """
놀이공원 매표소 안내판은 대기 번호를 재미있는 규칙으로 바꿔 보여 줘요. 번호가 짝수면 반으로 나누고, 홀수면 다섯 배 한 다음 1을 더합니다. 이 일을 번호가 1이 될 때까지 되풀이해요.
처음 번호 n은 1 이상 50만 이하의 정수예요. n이 6이라면 6 → 3 → 16 → 8 → 4 → 2 → 1로 여섯 번 바뀝니다.
1이 될 때까지 몇 번 바뀌는지 구해 주세요. 다만 200번을 바꿔도 1이 되지 않으면 -1이라고 답합니다."""),
    P("spaceship_rule", "repeat_rule", "우주선", """
우주선 연료 탱크의 압력 수치 p가 주어집니다. 안정 장치는 한 번 작동할 때마다 수치가 짝수이면 절반으로 줄이고, 홀수이면 5배로 올린 뒤 1을 더합니다.
수치가 1이 될 때까지 안정 장치가 작동한 횟수를 return 하도록 solution 함수를 완성하세요. 150번 작동해도 1이 되지 않으면 -1을 return 합니다.
제한사항
- p는 1 이상 3,000,000 이하의 정수입니다.
- 예: p가 12이면 12 → 6 → 3 → 16 → 8 → 4 → 2 → 1 이므로 7을 return 합니다."""),
]
BY_ID = {p["id"]: p for p in PROBLEMS}


def load_specs(cli: bool) -> dict:
    """문항 id → {text, spec, patterns, raw_patterns}. 캐시에 없거나 글이 바뀐 문항만 실제 프롬프트로 뽑는다."""
    cache = json.loads(SPECS.read_text(encoding="utf-8")) if SPECS.exists() else {}
    todo = [p for p in PROBLEMS if cache.get(p["id"], {}).get("text") != p["text"]]
    if not todo:
        return cache

    def one(p):
        got: Abstract = llm().use(abstract_text(p["text"]), Abstract, task="plan.abstract")
        # 그래프(plan/nodes.py)와 같게 온톨로지에 있는 id만 남긴다
        return {"text": p["text"], "spec": got.spec.strip(), "patterns": known_patterns(got.patterns), "raw_patterns": got.patterns}

    print(f"뼈대 뽑기: {len(todo)}개")
    with use_llm(ClaudeCli()) if cli else nullcontext():
        contexts = [copy_context() for _ in todo]
        with ThreadPoolExecutor(max_workers=4) as pool:
            rows = list(pool.map(lambda pair: pair[0].run(one, pair[1]), zip(contexts, todo)))
    cache.update({p["id"]: row for p, row in zip(todo, rows)})
    RESULTS.mkdir(exist_ok=True)
    SPECS.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    return cache


def fastembed_embedder(model: str):
    """측정용: fastembed 모델. 처음 부를 때 올린다(캐시에 없으면 내려받는다). 앱은 knowledge/embed.py의 모델 하나만 쓴다."""
    loaded = []

    def embed(texts: list[str]) -> list[list[float]]:
        if not loaded:
            from fastembed import TextEmbedding

            loaded.append(TextEmbedding(model))
        return [vector.tolist() for vector in loaded[0].embed(texts)]

    return embed


def openai_embedder():
    """측정용: text-embedding-3-small. app/llm의 공급자 코드를 부른다."""

    def embed(texts: list[str]) -> list[list[float]]:
        from ..llm.client import _backend_session

        _backend_session()
        from app.llm.openai.api_key.embed import embed as call

        return call(texts)

    return embed


def plain_embedder(model: str):
    if model == OPENAI:
        return openai_embedder()  # OPENAI_API_KEY가 있어야 한다
    return chargram_embedder() if model == CHARGRAM else fastembed_embedder(model)


def memo_embedder(model: str):
    """같은 글은 한 번만 임베딩한다. e5 계열은 양쪽 모두 'query: '를 붙인다(대칭 비교)."""
    base, prefix, seen = plain_embedder(model), "query: " if "e5" in model else "", {}

    def embed(texts):
        new = [text for text in dict.fromkeys(texts) if text not in seen]
        if new:
            seen.update(zip(new, base([prefix + text for text in new])))
        return [seen[text] for text in texts]

    return embed


def fill(index: ProblemIndex, texts: dict, specs: dict) -> None:
    for p in PROBLEMS:
        index.put(p["id"], texts[p["id"]], payload={"title": p["id"], "patterns": specs[p["id"]]["patterns"]})


def rank_all(index: ProblemIndex, texts: dict, specs: dict | None = None) -> dict:
    """질의 id → [(후보 id, 점수)]. specs를 주면 패턴을 넘긴다(색인의 점수식)."""
    return {
        p["id"]: [(row["problem_id"], row["score"]) for row in index.similar(
            texts[p["id"]], exclude=p["id"], limit=len(PROBLEMS), patterns=specs[p["id"]]["patterns"] if specs else None)]
        for p in PROBLEMS
    }


def rank_patterns(specs: dict, weight: float = 1.0) -> dict:
    """벡터 없이 패턴 겹침만. weight 0이면 모두 동점이라 무작위 줄 세우기가 된다."""
    return {p["id"]: [(o["id"], weight * overlap(specs[p["id"]]["patterns"], specs[o["id"]]["patterns"])) for o in PROBLEMS if o is not p]
            for p in PROBLEMS}


def measure(rankings: dict, queries: list[dict]) -> dict:
    rng = random.Random(0)
    p1 = rr = trap = 0.0
    for q in queries:
        rows = rankings[q["id"]]
        assert len(rows) == len(PROBLEMS) - 1, (q["id"], len(rows))
        for _ in range(SHUFFLES):
            order = [BY_ID[pid] for pid, _ in sorted(rows, key=lambda row: (-row[1], rng.random()))]
            p1 += order[0]["group"] == q["group"]
            trap += order[0]["story"] == q["story"]
            rr += 1 / next(i for i, other in enumerate(order, 1) if other["group"] == q["group"])
    n = len(queries) * SHUFFLES
    return {"p1": p1 / n, "mrr": rr / n, "trap": trap / n}


def cells(rankings: dict, halves: list[list[dict]]) -> str:
    return " | ".join("{p1:5.2f} {mrr:5.2f} {trap:5.2f}".format(**measure(rankings, half)) for half in halves)


def agreement(specs: dict) -> None:
    """같은 구조에 같은 패턴 id가 붙었는가. D팔의 천장이다."""
    print("\n패턴 일치(모델이 붙인 온톨로지 id)")
    same = any_ = pairs = 0
    for group in dict.fromkeys(p["group"] for p in PROBLEMS):
        members = [p for p in PROBLEMS if p["group"] == group]
        sets = [frozenset(specs[p["id"]]["patterns"]) for p in members]
        for i in range(len(sets)):
            for j in range(i + 1, len(sets)):
                pairs += 1
                same += sets[i] == sets[j]
                any_ += bool(sets[i] & sets[j])
        mark = "모두 같음" if len(set(sets)) == 1 else "다름"
        half = "개발" if group in DEV else "보류"
        print(f"  [{half}] {group:16} {mark:6} " + " / ".join(f"{p['story']}:{','.join(specs[p['id']]['patterns']) or '-'}" for p in members))
    cross = sum(bool(set(specs[a["id"]]["patterns"]) & set(specs[b["id"]]["patterns"]))
                for i, a in enumerate(PROBLEMS) for b in PROBLEMS[i + 1:] if a["group"] != b["group"])
    dropped = {pid: row["raw_patterns"] for pid, row in specs.items() if pid in BY_ID and row["raw_patterns"] != row["patterns"]}
    print(f"  같은 구조 쌍 {pairs}개: 패턴 집합이 똑같음 {same}, 하나라도 겹침 {any_} / 다른 구조인데 겹치는 쌍 {cross}개"
          f" / 온톨로지에 없는 id를 낸 문항 {len(dropped)}개 {dropped or ''}")


def model_files(model: str) -> tuple[float, bool]:
    """(캐시 폴더의 MB, 이미 받아 둔 모델인가)."""
    if model in (CHARGRAM, OPENAI):
        return 0.0, True
    from fastembed import TextEmbedding

    repo = next(m["sources"]["hf"] for m in TextEmbedding.list_supported_models() if m["model"] == model)
    root = Path(os.environ.get("FASTEMBED_CACHE_PATH") or Path(tempfile.gettempdir()) / "fastembed_cache") / ("models--" + repo.replace("/", "--"))
    size = sum(f.stat().st_size for f in (root / "snapshots").rglob("*") if f.is_file())  # 스냅숏의 링크를 따라가 실제 크기를 잰다
    return size / 1e6, size > 0


def latency(model: str, specs: dict) -> None:
    """색인에 이 모델을 주입해(메모 없음) 돌려 잰다. 첫 질의는 모델을 새로 올리는 시간을 포함한다."""
    texts = [specs[p["id"]]["spec"] for p in PROBLEMS]
    with tempfile.TemporaryDirectory() as path:
        index = ProblemIndex(path, embed=plain_embedder(model))
        began = time.perf_counter()
        index.put(PROBLEMS[0]["id"], texts[0])
        first_put = time.perf_counter() - began
        puts = []
        for p, text in zip(PROBLEMS[1:], texts[1:]):
            began = time.perf_counter()
            index.put(p["id"], text)
            puts.append(time.perf_counter() - began)
        index.close()
        began = time.perf_counter()
        index = ProblemIndex(path, embed=plain_embedder(model))  # 앱을 다시 켠 것처럼 모델을 새로 올린다
        index.similar(texts[0], limit=3)
        first = time.perf_counter() - began
        warm = []
        for text in texts:
            began = time.perf_counter()
            index.similar(text, limit=3, patterns=["dup_names"])
            warm.append(time.perf_counter() - began)
        index.close()
        disk = sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file())
    print(f"  시간: 첫 put {first_put:.2f}s(모델 올리기 포함), 이후 put 중앙값 {statistics.median(puts) * 1000:.1f}ms / "
          f"다시 연 뒤 첫 질의 {first:.2f}s, 이후 질의 중앙값 {statistics.median(warm) * 1000:.1f}ms 최대 {max(warm) * 1000:.1f}ms / "
          f"색인 폴더 {disk / 1e3:.0f}KB({len(PROBLEMS)}문항)")


def run_model(model: str, specs: dict, halves: list[list[dict]], detail: bool) -> None:
    _, cached = model_files(model)
    began = time.perf_counter()
    embed = memo_embedder(model)
    raw = {p["id"]: p["text"] for p in PROBLEMS}
    spec = {p["id"]: specs[p["id"]]["spec"] for p in PROBLEMS}
    dim = len(embed([PROBLEMS[0]["text"]])[0])
    load = time.perf_counter() - began
    size, _ = model_files(model)
    print(f"\n== {model} (차원 {dim}, 캐시 {size:.0f}MB, 처음 올리기 {load:.1f}s{'' if cached else ' — 내려받기 포함'}) ==")

    with tempfile.TemporaryDirectory() as raw_dir, tempfile.TemporaryDirectory() as spec_dir:
        raw_index, spec_index = ProblemIndex(raw_dir, embed=embed), ProblemIndex(spec_dir, embed=embed)
        fill(raw_index, raw, specs)
        fill(spec_index, spec, specs)

        grid = []
        for weight in GRID:
            spec_index.weight = weight
            rankings = rank_all(spec_index, spec, specs)
            grid.append((weight, measure(rankings, halves[0]), measure(rankings, halves[1])))
        best = max((dev["p1"], dev["mrr"]) for _, dev, _ in grid)
        tied = [weight for weight, dev, _ in grid if (dev["p1"], dev["mrr"]) == best]
        chosen = tied[(len(tied) - 1) // 2]
        print("  개발 절반에서 가중치 고르기(P@1/MRR): " + "  ".join(f"w={weight:g}:{dev['p1']:.2f}/{dev['mrr']:.2f}" for weight, dev, _ in grid))
        print(f"  → 가장 좋은 값들 {tied} 가운데 가운데 값 {chosen:g} (색인에 박힌 값 {knowledge_index.PATTERN_WEIGHT:g})")
        print("  참고(고르는 데 쓰지 않음) 보류 절반: " + "  ".join(f"w={weight:g}:{held['p1']:.2f}/{held['mrr']:.2f}" for weight, _, held in grid))

        spec_index.weight = knowledge_index.PATTERN_WEIGHT
        arms = {
            "A 문제 글 그대로": rank_all(raw_index, raw),
            "B 뼈대 명세": rank_all(spec_index, spec),
            f"C 명세+패턴(w={spec_index.weight:g})": rank_all(spec_index, spec, specs),
            "D 패턴 겹침만": rank_patterns(specs),
            "R 무작위": rank_patterns(specs, 0.0),
        }
        raw_index.close()
        spec_index.close()

    print(f"  {'팔':22} | " + " | ".join(f"{name:>4} P@1  MRR  함정" for name in ("개발", "보류", "전체")))
    for name, rankings in arms.items():
        print(f"  {name:22} | {cells(rankings, halves)}")
    if detail:
        for name, rankings in list(arms.items())[:3]:
            print(f"  -- {name}: 질의 → 1등")
            for q in PROBLEMS:
                top = BY_ID[max(rankings[q["id"]], key=lambda row: row[1])[0]]
                mark = "맞음" if top["group"] == q["group"] else "함정" if top["story"] == q["story"] else "틀림"
                print(f"     {q['id']:18} → {top['id']:18} {mark}")
    latency(model, specs)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cli", action="store_true")
    parser.add_argument("--model", action="append")
    parser.add_argument("--detail", action="store_true")
    args = parser.parse_args()

    for p in PROBLEMS:  # 세트 점검: 같은 이야기면 구조가 다르다, 모든 질의에 같은 구조와 같은 이야기 후보가 있다
        others = [o for o in PROBLEMS if o is not p]
        assert not any(o["group"] == p["group"] and o["story"] == p["story"] for o in others), p["id"]
        assert any(o["group"] == p["group"] for o in others) and any(o["story"] == p["story"] for o in others), p["id"]

    specs = load_specs(args.cli)
    began = time.perf_counter()
    import qdrant_client  # noqa: F401  fastembed가 깔려 있으면 qdrant_client가 fastembed까지 함께 올린다

    print(f"import 시간: qdrant_client(+fastembed) {time.perf_counter() - began:.2f}s")

    halves = [[p for p in PROBLEMS if p["group"] in DEV], [p for p in PROBLEMS if p["group"] not in DEV], PROBLEMS]
    print(f"문항 {len(PROBLEMS)}개: 개발 {len(halves[0])}(구조 {', '.join(DEV)}) / 보류 {len(halves[1])}. 후보는 늘 나머지 {len(PROBLEMS) - 1}개 전부")
    agreement(specs)
    if args.detail:
        for p in PROBLEMS:
            print(f"  {p['id']:18} {specs[p['id']]['spec']}")
    for model in args.model or MODELS:
        try:
            run_model(model, specs, halves, args.detail)
        except Exception as exc:  # 모델 하나가 안 올라가도 나머지는 잰다
            print(f"\n== {model}: 실패 {type(exc).__name__}: {str(exc)[:400]}")


if __name__ == "__main__":
    main()
