"""질문 유형 고르기. 의자·가이드의 규칙 표라 모델을 부르지 않는다."""

import re

from ..common.talk_rules import (ALL_FILLED, ANSWER_LEAD, BACK_LEAD, FALLBACK, FILL_TIP, REPLAN_LEAD, RETRY_LEAD, STUCK_LEAD,
                                open_lead, sentences)
from ..common.solution import shown_kind
from ..state import Block, BlockPlan, MovePlan, TurnContext, Verdict

LADDER = {"chair": ("open", "clue", "trace"), "guide": ("blank", "tool", "shape")}
LAST_MOVE = {"chair": "recap", "guide": "run"}
CLAIM_CHARS = 10  # 공백을 뺀 사용자 말이 이만큼이면 가정을 짚을 만한 주장으로 본다
CONFUSED = ("모르", "몰라", "감이 안", "헷갈", "막혔")  # 막힌 말은 반박(assume)이 아니라 사다리로 돕는다
OPENING = ("start", "next", "replan")  # 사용자 말 없이 블록의 첫 질문을 내는 사건
FOLLOW_UNTIL = 1  # 둘째 블록까지만 사용자 방법으로 다시 짠다. 뒤에서는 지금 계획으로 이어 간다
RUNG0 = ("replan",)  # 사다리 첫 칸으로 세는 다른 이름
FOUND_OK = "통과예요. 이 블록의 코드는 할 일을 해내요."  # 의자에서 이미 찾은 블록의 코드 확인이 통과했다(묻지 않는다. 동의로 시작하지 않는다)
# 저장 힌트를 1·2·3번까지 다 낸 뒤의 고정 말(3번을 되풀이하지 않는다)
HINTS_DONE = "이 블록의 힌트는 다 봤어요. 블록 칸에 적어 확인받거나, '이 블록 채우기'로 이 블록만 볼 수 있어요."
HINTS_DONE_UNFOUND = "이 블록의 힌트는 다 봤어요. '이 블록 채우기'로 이 블록만 볼 수 있어요."  # 의자에서 아직 찾지 못한 블록(코드 칸이 없다)
FOUND_TIP = "블록 칸에 이 블록의 코드를 적어 보세요. "  # 의자에서 말로 블록을 찾았을 때 앞말(찾은 블록의 칸에 적으라는 말이 없어 생각과 코드가 끊겼다)
_ASK_ANSWER = re.compile(r"답.{0,3}(알려|줘|주세요|보여)")


def signal_text(block: Block, miss: int | None) -> str:
    if miss and 1 <= miss <= len(block.checks):
        return block.checks[miss - 1]
    return block.checks[0] if block.checks else block.goal


def empty_answer(text: str) -> bool:
    """내용 없는 답: '모르겠어요', '잘 모르겠음', '글쎄요', '힌트 주세요', '...'처럼 짧고 생각이 담기지 않은 말."""
    plain = re.sub(r"\s+", "", text or "")
    return 0 < len(plain) < CLAIM_CHARS and (any(word in plain for word in (*CONFUSED, "글쎄", "힌트")) or not re.search(r"[가-힣A-Za-z0-9]", plain))


def rule_verdict(text: str) -> Verdict | None:
    """모델 없이 가르는 내용 없는 말: 짧은 답 요청('답 알려 주세요')은 A, '모르겠어요'·'힌트' 류는 N. 그 밖은 None(모델이 판정한다)."""
    plain = re.sub(r"\s+", "", text or "")
    if 0 < len(plain) < 15 and _ASK_ANSWER.search(plain):
        return Verdict(False, aside="A")
    return Verdict(False) if empty_answer(text) else None


def found_tip(mode: str, turn: TurnContext, move: MovePlan) -> str:
    """의자에서 말로 지금 블록을 찾았으면 찾은 블록에 남길 안내(FOUND_TIP). 다음 블록의 질문과 다른 말로 남긴다(한 말에 붙어 다음 블록 아래에 보였다)."""
    return FOUND_TIP.strip() if mode == "chair" and turn.event == "message" and move.advance else ""


def pick_move(mode: str, plan: BlockPlan, turn: TurnContext, verdict: Verdict | None, allow_follow: bool = True, found: bool = False, language: str = "python") -> MovePlan:
    """found: 의자에서 이미 찾은 블록의 코드 확인(맞는지만 알리고 진행은 그대로).
    같은 블록에서 내용 없는 답이 두 번 이어지면 그 말 앞에 '이 블록 채우기' 안내를 한 번 붙인다('모르겠어요' 세 번에도 길을 몰랐다).
    의자에서 말로 블록을 찾아 넘어갈 때 찾은 블록의 칸에 코드를 적어 보라는 말(FOUND_TIP)은 그래프가 찾은 블록의 말로 따로 남긴다(found_tip)."""
    move = _pick_move(mode, plan, turn, verdict, allow_follow, found, language)
    if (turn.event == "message" and not move.advance and not turn.tipped and "이 블록 채우기" not in move.lead + (move.saved or "")
            and empty_answer(turn.text) and empty_answer(turn.previous)):
        move.lead = FILL_TIP + move.lead
    return move


def _pick_move(mode: str, plan: BlockPlan, turn: TurnContext, verdict: Verdict | None, allow_follow: bool, found: bool, language: str) -> MovePlan:
    blocks, index = plan.blocks, turn.index
    used = turn.moves_used

    def ladder(lead: str = "", signal: str = "") -> MovePlan:
        """모델이 짓는 사다리 질문: 사용자가 내용 있는 말을 했거나, 저장 힌트가 없는 옛 계획."""
        level = min(sum(move in LADDER[mode] or move in RUNG0 for move in used), 2)
        if not lead and used.count(LADDER[mode][-1]) >= 2:
            lead = STUCK_LEAD  # 꼭대기 질문을 두 번 받고도 막혔다: 빠져나갈 길을 알려 준다
        name = "replan" if turn.event == "replan" else LADDER[mode][level]  # replan은 저장 기록에서 새 계획의 시작 표시다
        return MovePlan(name, index, False, lead, None, signal)

    def hinted(lead: str = "", signal: str = "") -> MovePlan:
        """저장 힌트의 다음 번호(모델 0회): 블록을 여는 말, 내용 없는 답('모르겠어요', 답 요청, 무관한 말) 뒤. 다 냈으면 고정 말.
        모델이 지은 안내 말은 원칙을 어기곤 했다(답을 말함). 저장 힌트가 없는 옛 계획은 모델이 짓는다.
        블록 코드 확인이 N일 때도 이 자리를 쓴다: 확인 항목(checks)은 답을 말한 문장이라 인용하지 않는다."""
        hints, seen = blocks[index].hints, turn.hints_seen
        if not hints:
            return ladder(lead, signal)
        if seen >= len(hints):  # 고정 말이 '이 블록 채우기'를 알리니 같은 안내를 앞말에서 뺀다
            kept = " ".join(part for part in sentences(lead) if "이 블록 채우기" not in part)
            return MovePlan(LADDER[mode][-1], index, False, kept + " " if kept else "", HINTS_DONE_UNFOUND if mode == "chair" and not found else HINTS_DONE)
        return MovePlan("replan" if turn.event == "replan" else LADDER[mode][min(seen, 2)], index, False, lead, hints[seen])

    def advance() -> MovePlan:
        if index + 1 >= len(blocks) and mode == "guide" and turn.event == "block_filled":
            return MovePlan("done", index, True, saved=ALL_FILLED)  # 가이드 마지막 블록 코드가 통과했다: 진행 안내만, 묻지 않는다
        if index + 1 >= len(blocks):
            return MovePlan(LAST_MOVE[mode], index, True)
        return MovePlan(LADDER[mode][0], index + 1, True, open_lead(mode, shown_kind(blocks[index + 1], language)), (blocks[index + 1].hints or [None])[0])

    if turn.event in OPENING:
        return hinted({"start": "", "replan": REPLAN_LEAD}.get(turn.event, open_lead(mode, shown_kind(blocks[index], language))))
    if (mode == "chair" and turn.event == "message" and verdict is not None and verdict.other
            and allow_follow and index <= FOLLOW_UNTIL and not turn.followed_before):
        return MovePlan("replan", index, False)  # 말이 아니라 '사용자 방법으로 다시 짜기' 요청이다
    if turn.event == "message" and verdict is not None and verdict.aside:
        return hinted(ANSWER_LEAD if verdict.aside == "A" else BACK_LEAD)  # 고정 앞말 뒤에 다음 저장 힌트
    if turn.event == "message" and index == len(blocks) - 1 and (LAST_MOVE[mode] in used or "done" in used):
        return MovePlan("close", index, False, saved=FALLBACK["close"])  # 정리 질문에 답했다: 같은 질문을 되풀이하지 않고 코드로 보낸다
    if mode == "chair" and turn.event == "message" and used[-1:] == ["basis"]:
        return advance()  # 이미 찾은 블록의 근거 질문에 답했다. 답을 다시 판정하지 않는다
    if turn.event == "message" and empty_answer(turn.text):
        return hinted()  # 내용 없는 답: 모델이 짓지 않는다
    ok = bool(verdict and verdict.ok)
    if turn.event == "block_filled":
        # 고정 앞말 뒤에 실행에서 본 것 한 줄, 그다음 저장 힌트(저장 힌트만으로는 그 코드의 문제와 상관없는 말이 많았다)
        lead = RETRY_LEAD + (f"{verdict.seen} " if verdict and verdict.seen else "")
        if verdict is not None and verdict.unsure:
            lead = f"{verdict.seen} "  # 확인하지 못했다(거부가 아니다): '이 코드로는 아직 넘어가지 않아요'라 하지 않는다
        # 문법·실행 오류, 괄호·들여쓰기 안내, 이름 찾기 실패에는 저장 힌트를 붙이지 않는다(오타 뒤에 전략 질문이 붙었다). 힌트 번호도 쓰지 않는다
        plain = not ok and verdict is not None and not verdict.hint
        if found:  # 의자에서 이미 찾은 블록: 맞는지만 알리고 진행은 그대로
            retry = hinted(lead)
            return MovePlan("done", index, False, saved=FOUND_OK if ok else (retry.lead + retry.saved if retry.saved and not plain else lead.strip()))
        if plain:
            return MovePlan(LADDER[mode][min(turn.hints_seen, 2)], index, False, saved=lead.strip())
        # 저장 힌트가 없으면 못 해낸 첫 신호를 겨눠 짓는다(빠진 것과 다른 것을 물었다)
        return advance() if ok else hinted(lead, signal_text(blocks[index], verdict.miss if verdict else None))
    if ok:
        # 근거 질문은 문항에 한 번, 생각할 거리가 있는 블록(반복·조건·분기)에서만 한다.
        # '답 담을 리스트' 같은 변수 블록마다 근거를 물으니 초보자가 멈칫했다(같은 질문이 두 블록 연달아 나왔다)
        if (mode == "chair" and (verdict.basis or "g") == "g" and not turn.basis_asked
                and blocks[index].kind in ("loop", "condition", "branch")):
            return MovePlan("basis", index, False)
        return advance()
    if mode == "chair" and verdict is not None and not verdict.malformed:  # 형식 오류는 사다리
        miss = verdict.miss
        if miss and miss >= 2:
            return MovePlan("edge", index, False, missing_signal=signal_text(blocks[index], miss))
        claim = len(re.sub(r"\s+", "", turn.text)) >= CLAIM_CHARS and not any(word in turn.text for word in CONFUSED)
        if claim and (used[-1] if used else None) not in ("assume", "edge"):
            return MovePlan("assume", index, False, missing_signal=signal_text(blocks[index], miss))
    return ladder()
