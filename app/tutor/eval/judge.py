"""평가기 2층: 모델 평가기. 규칙으로 못 보는 것(뜻으로 새는 답, 초보자 눈높이, 사실 정확성, 판정 적합성)을 본다.

신뢰를 위한 장치
1. 기준마다 pass·fail·na 셋 중 하나(점수 척도 대신 이진 판정. 정의와 경계 예시를 프롬프트에 둔다).
2. fail은 근거 인용이 필수이고, 인용은 튜터 말(판정 기준은 사용자 말)에 글자 그대로 있어야 한다. 없으면 그 표는 무효다.
3. 같은 입력을 k번 따로 묻고 다수결. 표가 갈리면 불안정으로 표시한다.
4. 기준마다 보정 세트(calibrate.py)의 정확도·카파가 문턱을 넘어야 판단에 쓴다(trusted).
5. 평가기는 개선 전·후 어느 판인지 모른다(기록에 판 정보를 넣지 않는다).
"""

import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context

from ..llm import llm, themes

JUDGE_MODEL_ENV = "ALGOBLOCK_EVAL_JUDGE_MODEL"
LABELS = ("pass", "fail", "na")

CRITERIA = {
    "leak": (
        "답 유출. 사용자가 아직 말하지 않은 이 블록의 답을 튜터가 먼저 알려 주면 fail.\n"
        "- 의자(chair): 참고 코드, 핵심 자료구조·기법의 이름(예: 딕셔너리로, 스택에 넣고), 목표를 지시문으로 말하기(예: 이름마다 개수를 세세요)는 fail.\n"
        "- 가이드(guide): 빈칸을 이끄는 모드라 쓸 자료구조·연산의 이름과, 빈칸의 모양을 말로 보여 주는 것(예: 이름을 키로, 횟수를 값으로)은 허용. "
        "코드 한 줄이나 빈칸에 들어갈 식을 그대로 쓰면 fail.\n"
        "- 디버그(debug): 사용자가 쓴 코드의 틀린 곳을 스스로 찾게 돕는 모드다. 고친 코드 줄을 쓰거나 무엇을 무엇으로 바꿀지를 그대로 말하면 fail. "
        "실패한 입력과 기대한 값·실제 값, 오류 메시지의 뜻, 줄 번호를 알려 주는 것, 같은 문법을 이 문제와 상관없는 다른 예로 보여 주는 것은 허용. "
        "앞 대화에서 사용자가 여러 번 막힌 뒤라면 무엇이 왜 틀렸는지 말로 설명하는 것도 허용(고친 코드는 안 됨).\n"
        "- '다음은 '반복' 블록이에요'처럼 블록의 종류(변수·반복·조건·분기)만 알려 주는 이음말은 유출이 아니다.\n"
        "- 문제 글 문장을 인용하거나 작은 예시를 따라가게 묻는 것은 유출이 아니다. 사용자가 이미 말한 것을 되짚는 것도 아니다."
    ),
    "responsive": (
        "반응. 사용자의 직전 말(주장, 오해, 질문, 모르겠다는 말)을 받아서 이어 가면 pass. 사용자 말과 상관없는 일반 질문만 하면 fail.\n"
        "- 사용자가 '모르겠어요'라고 했는데 같은 질문을 되풀이하거나 더 어려운 질문을 하면 fail.\n"
        "- fail의 근거는 튜터 말이나, 튜터가 받지 않은 사용자 말 중 결정적인 구절이다.\n"
        "- 사용자 말이 없는 요청(시작, 다음 블록을 연 첫 말)이면 na."
    ),
    "novice_fit": (
        "초보자 눈높이. 아래 중 하나라도 있으면 fail.\n"
        "- 서로 다른 질문을 둘 이상 한다(선택지 두 개를 주는 한 질문은 괜찮다).\n"
        "- 초보자가 모를 용어(예: 해시맵, 시간복잡도, O(n), 오버헤드)를 풀이 없이 쓴다.\n"
        "- 무엇을 대답해야 할지(값, 방법, 이유 중 무엇인지) 알 수 없다."
    ),
    "grounded": (
        "사실 정확성. 문제 글·입출력 예와 어긋나는 말(틀린 예시 값, 없는 조건, 바뀐 조건)을 사실처럼 하면 fail. 질문 속 가정 상황은 fail이 아니다."
    ),
    "verdict": (
        "판정 적합. 판정한 블록(따로 없으면 지금 블록)의 목표와 1번 신호를 사용자 말이 자기 말로 담았는지 네가 직접 판단하고, 시스템 판정과 같으면 pass, 다르면 fail.\n"
        "- 변수 이름이나 코드가 정확하지 않아도 역할을 맞게 말했으면 '찾음'이 옳다. 방향만 맞고 1번 신호가 빠졌으면 '못 찾음'이 옳다.\n"
        "- fail이면 근거로 사용자 말에서 결정적인 구절을 인용한다(사용자 말이 판단 근거다).\n"
        "- 사용자 말이 없는 요청이면 na."
    ),
}

# fail의 근거를 어디서 찾아야 하는가
EVIDENCE_IN = {"leak": "reply", "responsive": "either", "novice_fit": "reply", "grounded": "reply", "verdict": "user"}

SYSTEM = (
    "너는 코딩테스트 튜터의 대화 품질을 판정하는 평가자다. 튜터는 답을 대신 알려 주지 않고 초보자가 스스로 찾게 묻는 것이 목표다.\n"
    "기준마다 정의만 보고 판단한다. 말투가 친절한지, 길이가 적당한지는 보지 않는다. 확신이 없으면 pass 쪽으로 기운다."
)


def judge_messages(item: dict) -> list[dict]:
    """item: problem, mode, block{name, goal, checks, reference}, context[], user, reply, decision."""
    block = item["block"]
    checks = "\n".join(f"{n}. {c}" for n, c in enumerate(block.get("checks") or [], 1)) or "없음"
    lines = [
        f"문제:\n{item['problem']}",
        f"모드:{item['mode']}",
        f"지금 블록:{block['name']}",
        f"블록 목표(사용자가 찾아야 할 것, 사용자에게 보이지 않음):{block['goal']}",
        f"신호:\n{checks}",
        f"참고 코드(사용자에게 보이지 않음. 디버그에서는 고친 줄):\n{block.get('reference', '')}",
        *([f"사용자가 쓴 코드:\n{item['code']}"] if item.get("code") else []),
        "앞 대화:",
        *(item.get("context") or ["없음"]),
        *([f"판정한 블록(사용자 말이 해당하는 블록, 시스템 판정의 대상):{item['judged']['name']}",
           f"판정한 블록 목표:{item['judged']['goal']}",
           "판정한 블록 신호:\n" + ("\n".join(f"{n}. {c}" for n, c in enumerate(item['judged'].get('checks') or [], 1)) or "없음")]
          if item.get("judged") else []),
        f"사용자 말:{item.get('user') or '(없음)'}",
        f"시스템 판정:{item.get('decision') or '(해당 없음)'}",
        f"튜터 말:{item['reply']}",
        "",
        "기준:",
        *[f"[{name}] {text}" for name, text in CRITERIA.items()],
        "",
        "출력: JSON 한 개만. 키는 기준 이름. 값은 {\"label\": \"pass|fail|na\", \"evidence\": \"fail이면 근거 구절을 글자 그대로\", \"reason\": \"한 문장\"}.",
    ]
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "\n".join(lines)}]


def parse_vote(text: str) -> dict | None:
    raw = (text or "").strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text or "").strip("'\"‘’“”")


def valid_label(name: str, entry, item: dict) -> str | None:
    """표 하나를 검증한다. 무효면 None."""
    if not isinstance(entry, dict) or entry.get("label") not in LABELS:
        return None
    label = entry["label"]
    if label == "fail":
        where = EVIDENCE_IN[name]
        sources = [item.get("user"), item.get("reply")] if where == "either" else [item.get(where)]
        quote = _squash(entry.get("evidence") or "")
        if not quote or not any(quote in _squash(text or "") for text in sources):
            return None  # 근거 없는 fail은 믿지 않는다
    return label


def tally(votes: list[dict | None], item: dict) -> dict:
    """기준마다 다수결. {name: {label, agree, valid, reasons}}. 과반이 없으면 uncertain."""
    out = {}
    for name in CRITERIA:
        labels, reasons = [], []
        for vote in votes:
            entry = (vote or {}).get(name)
            label = valid_label(name, entry, item)
            if label is not None:
                labels.append(label)
                if label == "fail":
                    reasons.append(f"{entry.get('evidence')} — {entry.get('reason', '')}")
        if not labels:
            out[name] = {"label": "uncertain", "agree": 0.0, "valid": 0, "reasons": []}
            continue
        top, top_count = Counter(labels).most_common(1)[0]
        majority = top_count * 2 > len(votes)
        out[name] = {
            "label": top if majority else "uncertain",
            "agree": round(top_count / len(labels), 2),
            "valid": len(labels),
            "reasons": reasons[:2],
        }
    return out


def judge(item: dict, k: int = 3, model: str | None = None) -> dict:
    """같은 입력을 k번 따로 묻는다(병렬). 모델 오류 표는 무효로 센다."""
    import os

    name = model or os.environ.get(JUDGE_MODEL_ENV) or themes.model_of("middle")  # 튜터의 판정(작음)보다 센 모델이어야 평가를 믿는다
    messages = judge_messages(item)

    def one(_):
        try:
            return parse_vote(llm(name).use(messages, None, task="eval.judge"))
        except Exception:  # noqa: BLE001 - 평가기 실패는 무효 표
            return None

    contexts = [copy_context() for _ in range(k)]  # 부른 스레드의 use_llm(가짜·CLI)을 일꾼 스레드로 넘긴다
    with ThreadPoolExecutor(max_workers=k) as pool:
        votes = list(pool.map(lambda pair: pair[0].run(one, pair[1]), zip(contexts, range(k))))
    return tally(votes, item)
