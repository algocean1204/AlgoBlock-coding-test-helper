"""판정 노드의 짧은 출력. JSON 대신 [check] 한 줄로 받는다.

[check]Y          맞음
[check]N2         아님. 2번 신호가 빠짐
[check]Y g        맞음, 근거 수준 g(의자 말 판정만)
[check]72 Y       채점. 점수와 방향
[check]D          계획과 다른 방법인데 그 방법으로도 풀린다(의자 말 판정만)
[check]A, [check]O 답을 달라는 요청, 문제와 무관한 말(의자·가이드 말 판정만)
[check]Q          자기 생각이 아니라 튜터 말·문제·문법·개념을 되묻는 말(의자·가이드 말 판정만). 옛 W(낱말 뜻)도 Q로 읽는다
"""

import re

from ..llm import llm, model_name
from ..state import Verdict

MAX_TOKENS = 16
_PATTERN = re.compile(r"\[check\]\s*(?:(\d{1,3})\s+)?([YNDAOQW])\s*(\d)?\s*([teg])?", re.IGNORECASE)


def parse_verdict(text: str | None) -> Verdict | None:
    """처음 나온 [check] 한 개만 본다. 없으면 None."""
    found = _PATTERN.search(text or "")
    if found is None:
        return None
    score, mark, miss, basis = found.groups()
    mark = "Q" if mark.upper() == "W" else mark.upper()
    ok = mark == "Y"
    return Verdict(
        other=mark == "D",
        aside=mark if mark in "AOQ" else "",
        ok=ok,
        miss=None if ok or miss is None else int(miss),
        basis=basis.lower() if basis else None,
        score=None if score is None else int(score),
    )


def ask_verdict(messages: list[dict], rule: str, task: str) -> Verdict | None:
    """출력 형식 rule을 마지막 메시지 끝에 붙여 한 번 부른다. 형식이 틀리면 None."""
    last = messages[-1]
    asked = [*messages[:-1], {**last, "content": f"{last['content']}\n\n{rule}"}]
    text = llm(model_name()).use(asked, None, task=task, max_tokens=MAX_TOKENS)
    return parse_verdict(text)


FOUND_RULE = "출력 형식: 맞으면 [check]Y, 아니면 [check]N 뒤에 가장 먼저 빠진 신호 번호(예: [check]N1). 이 한 줄만 쓴다."
BASIS_RULE = (
    "출력 형식: [check]결과 근거. 결과는 Y, 또는 N 뒤에 가장 먼저 빠진 신호 번호(예: N1), 또는 D(다른 방법). "
    "근거는 t, e, g 중 하나(예: [check]Y g, [check]N1 t, [check]D g). 이 한 줄만 쓴다."
)
ASIDE_RULE = " 사용자 말이 답이나 답 코드를 달라는 요청이면 [check]A, 지금 문제와 무관한 말이면 [check]O로 쓴다."
# 되묻는 말(낱말 뜻, 문법, 문제 글, 튜터 말, 개념)을 갈라 먼저 답한 뒤 원래 질문으로 돌아간다(turn/moves.py의 term). 판정 호출 하나로 가른다.
# 꼴(물음표, 말끝)이 아니라 무엇을 묻는지로 가른다: 모르는 것을 알려 달라는 말은 Q, 자기 생각을 내놓고 맞는지 묻는 말은 판정 기준대로
TERM_RULE = (" Y·N을 가리기 전에 되묻는 말인지 먼저 본다. 사용자 말이 자기 생각을 낸 것이 아니라 튜터 말·문제·문법·개념에서 모르는 것을 알려 달라는 말이면 [check]Q로 쓴다."
             " 물음표가 없어도 같다. 모른다·궁금하다·이해가 안 된다고 하며 알고 싶은 것을 밝힌 말도 Q다."
             " Q인 것: 낱말 뜻, 튜터 말이 무슨 뜻인지, 문제 글의 뜻·까닭이나 조건(입력 범위, 경계 경우, 무엇을 포함하고 허용하는지)을 확인하는 말,"
             " 언어 문법·기본 기능을 어떻게 쓰는지나 그렇게 쓰면 어떻게 되는지 묻는 말, 자료구조·알고리즘 개념이 무엇인지나 어떻게·왜 그런지 묻는 말."
             " 문법·개념은 이 블록과 바로 닿지 않아도 Q다."
             " 자기 생각(이 블록에서 할 방법·값·조건·코드)을 내놓고 맞는지 묻는 말은 물음표나 말끝이 어떻든 Q가 아니라 위 기준대로 판정한다."
             " 튜터 질문은 알아들었지만 답을 모르겠다는 말도 Q가 아니다. 코딩·문제와 무관한 물음은 O다.")
SCORE_RULE = "출력 형식: [check]점수 방향. 점수는 0–100 정수, 방향이 맞으면 Y 아니면 N(예: [check]72 Y). 이 한 줄만 쓴다."
