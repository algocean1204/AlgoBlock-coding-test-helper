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
# 되묻는 말(낱말 뜻, 문법, 문제 글, 튜터 말)을 갈라 먼저 답한 뒤 원래 질문으로 돌아간다(turn/moves.py의 term). 판정 호출 하나로 가른다
TERM_RULE = (" 사용자 말이 자기 생각을 낸 것이 아니라 튜터 말·문제·문법·개념을 되묻는 말이면(예: '그게 뭐예요?', '이 문법은 어떻게 써요?') [check]Q로 쓴다."
             " 자기 생각을 물음 꼴로 낸 말('~하면 되나요?')은 Q가 아니라 위 기준대로 판정한다.")
SCORE_RULE = "출력 형식: [check]점수 방향. 점수는 0–100 정수, 방향이 맞으면 Y 아니면 N(예: [check]72 Y). 이 한 줄만 쓴다."
