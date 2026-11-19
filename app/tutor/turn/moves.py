"""질문 유형 고르기. 의자·가이드의 규칙 표라 모델을 부르지 않는다."""

import re

from ..common.talk_rules import (ALL_FILLED, ANSWER_LEAD, BACK_LEAD, FALLBACK, FILL_TIP, HARD_LEAD, REPLAN_LEAD, RETRY_LEAD, STUCK_LEAD,
                                open_lead, sentences)
from ..common.solution import shown_kind
from ..state import Block, BlockPlan, MovePlan, TurnContext, Verdict

LADDER = {"chair": ("open", "clue", "trace"), "guide": ("blank", "tool", "shape")}
LAST_MOVE = {"chair": "recap", "guide": "run"}
CLAIM_CHARS = 10  # 공백을 뺀 사용자 말이 이만큼이면 가정을 짚을 만한 주장으로 본다
CONFUSED = ("모르", "몰라", "감이 안", "헷갈", "막혔")  # 막힌 말은 반박(assume)이 아니라 사다리로 돕는다
# 어렵다는 말: 같은 질문을 되풀이하지 않고 더 작게 나눈다. '어려' 부분 일치는 '어려운 건 없고…'에도 걸렸다: 어렵다고 말한 꼴만 보고, 아니라는 말은 뺀다
HARD = re.compile(r"어려워|어렵(?:네|다|습|고|어|더|기)|이해가?\s*안\s*(?:돼|되|가)")
NOT_HARD = re.compile(r"어려운\s*(?:건|게|것은?|점은?)\s*없|안\s*어려|어렵지\s*않|어렵진\s*않")
# 뜻을 묻는 말의 표지. '그게 뭔지 몰라요'가 '모르겠어요'로 끊겨 판정(Q)에 가지 못했다
TERM_ASK = re.compile(r"뭔지|뭐예요|뭐에요|뭐야|뭔가요|무슨\s*뜻|무슨\s*말")
OPENING = ("start", "next", "replan")  # 사용자 말 없이 블록의 첫 질문을 내는 사건
FOLLOW_UNTIL = 1  # 둘째 블록까지만 사용자 방법으로 다시 짠다. 뒤에서는 지금 계획으로 이어 간다
RUNG0 = ("replan",)  # 사다리 첫 칸으로 세는 다른 이름
FOUND_OK = "통과예요. 이 블록의 코드는 할 일을 해내요."  # 의자에서 이미 찾은 블록의 코드 확인이 통과했다(묻지 않는다. 동의로 시작하지 않는다)
# 저장 힌트를 1·2·3번까지 다 낸 뒤의 고정 말(3번을 되풀이하지 않는다). 의자의 찾기 전 블록에도 코드 칸이 있어 두 방식이 같다
HINTS_DONE = "이 블록의 힌트는 다 봤어요. 블록 칸에 적어 확인받거나, '이 블록 채우기'로 이 블록만 볼 수 있어요."
# 말로 맞혔다. 다음 블록은 블록 코드 확인(또는 넘어가기·채우기)으로만 열린다(말로 열면 코드 칸이 빈 채 지나갔다). 의자·가이드 같다
WRITE_TIP = "그 생각을 이 블록의 코드 칸에 코드로 적고 '블록 코드 확인'을 눌러 보세요. 확인을 통과하면 다음 블록이 열려요."
WRITE_TIP_LAST = "그 생각을 이 블록의 코드 칸에 코드로 적고 '블록 코드 확인'을 눌러 보세요. 마지막 블록이라, 확인을 통과하면 모은 코드로 풀이를 돌려 볼 수 있어요."
_ASK_ANSWER = re.compile(r"(?<!기대)(?<!예상)(?<!실제)(?<!출력)답.{0,3}(알려|줘|주세요|보여)")  # '기대 답 보여줘'(기대한 값을 묻는 말)는 답 요청이 아니다
# 튜터에게 묻는 말의 끝(물음표, '~하나요', '~인가요', '~할까요', '~죠'). 물음 어미만 본다: '세어 가요', '하니까'는 평서문이다
_ASKS = re.compile(r"(?:[?？]|나요|(?:인|는|건|은|던)가요|(?<!니)까요?|죠|는지요)[\s.!~]*$")


def asks(text: str) -> bool:
    """사용자 말이 튜터에게 묻는 꼴인가. 판정은 질문 꼴이어도 생각이 맞으면 Y라, 이것으로 물음과 말한 생각을 나눈다."""
    return bool(_ASKS.search((text or "").strip()))


def hard(text: str) -> bool:
    """사용자가 어렵다고 했는가('너무 어려워요', '이해가 안 돼요'). '어려운 건 없고', '어렵지 않아요'는 아니다."""
    return bool(HARD.search(text or "")) and not NOT_HARD.search(text or "")


def signal_text(block: Block, miss: int | None) -> str:
    if miss and 1 <= miss <= len(block.checks):
        return block.checks[miss - 1]
    return block.checks[0] if block.checks else block.goal


def empty_answer(text: str) -> bool:
    """내용 없는 답: '모르겠어요', '잘 모르겠음', '글쎄요', '힌트 주세요', '너무 어려워요', '...'처럼 짧고 생각이 담기지 않은 말.
    뜻을 묻는 말('그게 뭔지 몰라요')은 내용 없는 답이 아니다(판정이 뜻 묻기로 가른다)."""
    plain = re.sub(r"\s+", "", text or "")
    if TERM_ASK.search(text or ""):
        return False
    return 0 < len(plain) < CLAIM_CHARS and (any(word in plain for word in (*CONFUSED, "글쎄", "힌트")) or hard(text)
                                             or not re.search(r"[가-힣A-Za-z0-9]", plain))


def rule_verdict(text: str) -> Verdict | None:
    """모델 없이 가르는 내용 없는 말: 짧은 답 요청('답 알려 주세요')은 A, '모르겠어요'·'힌트' 류는 N. 그 밖은 None(모델이 판정한다)."""
    plain = re.sub(r"\s+", "", text or "")
    if 0 < len(plain) < 15 and _ASK_ANSWER.search(plain):
        return Verdict(False, aside="A")
    return Verdict(False) if empty_answer(text) else None


def pick_move(mode: str, plan: BlockPlan, turn: TurnContext, verdict: Verdict | None, allow_follow: bool = True, found: bool = False, language: str = "python") -> MovePlan:
    """found: 의자에서 이미 찾은 블록의 코드 확인(맞는지만 알리고 진행은 그대로).
    같은 블록에서 내용 없는 답이 두 번 이어지면 '이 블록 채우기' 안내를 길 안내 줄로 한 번 붙인다('모르겠어요' 세 번에도 길을 몰랐다).
    말로는 다음 블록을 열지 않는다: 말로 맞히면 그 블록의 코드 칸에 적으라는 고정 말(write)이다."""
    move = _pick_move(mode, plan, turn, verdict, allow_follow, found, language)
    if (turn.event == "message" and not move.advance and not turn.tipped and "이 블록 채우기" not in move.lead + move.way + (move.saved or "")
            and empty_answer(turn.text) and empty_answer(turn.previous)):
        move.way = FILL_TIP
    return move


def _pick_move(mode: str, plan: BlockPlan, turn: TurnContext, verdict: Verdict | None, allow_follow: bool, found: bool, language: str) -> MovePlan:
    blocks, index = plan.blocks, turn.index
    used = turn.moves_used

    def ladder(lead: str = "", signal: str = "", way: str = "") -> MovePlan:
        """모델이 짓는 사다리 질문: 사용자가 내용 있는 말을 했거나, 저장 힌트가 없는 옛 계획."""
        level = min(sum(move in LADDER[mode] or move in RUNG0 for move in used), 2)
        if not lead and not way and used.count(LADDER[mode][-1]) >= 2:
            way = STUCK_LEAD  # 꼭대기 질문을 두 번 받고도 막혔다: 빠져나갈 길을 알려 준다
        name = "replan" if turn.event == "replan" else LADDER[mode][level]  # replan은 저장 기록에서 새 계획의 시작 표시다
        return MovePlan(name, index, False, lead, None, signal, way)

    def hinted(lead: str = "", signal: str = "", way: str = "") -> MovePlan:
        """저장 힌트의 다음 번호(모델 0회): 블록을 여는 말, 내용 없는 답('모르겠어요', 답 요청, 무관한 말) 뒤. 다 냈으면 고정 말.
        모델이 지은 안내 말은 원칙을 어기곤 했다(답을 말함). 저장 힌트가 없는 옛 계획은 모델이 짓는다.
        블록 코드 확인이 N일 때도 이 자리를 쓴다: 확인 항목(checks)은 답을 말한 문장이라 인용하지 않는다."""
        hints, seen = blocks[index].hints, turn.hints_seen
        if not hints:
            return ladder(lead, signal, way)
        if seen >= len(hints):  # 고정 말이 '이 블록 채우기'를 알리니 같은 안내를 앞말·길 안내에서 뺀다
            kept = [" ".join(part for part in sentences(text) if "이 블록 채우기" not in part) for text in (lead, way)]
            return MovePlan(LADDER[mode][-1], index, False, kept[0] + " " if kept[0] else "", HINTS_DONE, way=kept[1])
        return MovePlan("replan" if turn.event == "replan" else LADDER[mode][min(seen, 2)], index, False, lead, hints[seen], way=way)

    def advance() -> MovePlan:
        if index + 1 >= len(blocks) and mode == "guide" and turn.event == "block_filled":
            return MovePlan("done", index, True, saved=ALL_FILLED, fact=True)  # 가이드 마지막 블록 코드가 통과했다: 진행 안내만, 묻지 않는다
        if index + 1 >= len(blocks):
            return MovePlan(LAST_MOVE[mode], index, True)
        return MovePlan(LADDER[mode][0], index + 1, True, open_lead(mode, shown_kind(blocks[index + 1], language)), (blocks[index + 1].hints or [None])[0])

    def write() -> MovePlan:
        return MovePlan("write", index, False, saved=WRITE_TIP_LAST if index == len(blocks) - 1 else WRITE_TIP, fact=True)  # 물음이 아닌 안내라 칸으로는 결과다

    if turn.event in OPENING:
        return hinted({"start": "", "replan": REPLAN_LEAD}.get(turn.event, open_lead(mode, shown_kind(blocks[index], language))))
    if (mode == "chair" and turn.event == "message" and verdict is not None and verdict.other
            and allow_follow and index <= FOLLOW_UNTIL and not turn.followed_before):
        return MovePlan("replan", index, False)  # 말이 아니라 '사용자 방법으로 다시 짜기' 요청이다
    if turn.event == "message" and verdict is not None and verdict.aside == "Q":
        return MovePlan("term", index, False)  # 되물었다(낱말 뜻, 문법, 문제 글): 모델이 먼저 답한 뒤 원래 질문으로 돌아간다. 사다리 칸·힌트 번호를 쓰지 않는다
    if turn.event == "message" and verdict is not None and verdict.aside:
        return hinted(way=ANSWER_LEAD) if verdict.aside == "A" else hinted(BACK_LEAD)  # 다음 저장 힌트. 답을 주지 않는다는 말은 길 안내 줄로
    if turn.event == "message" and index == len(blocks) - 1 and (LAST_MOVE[mode] in used or "done" in used):
        return MovePlan("close", index, False, saved=FALLBACK["close"])  # 정리 질문에 답했다: 같은 질문을 되풀이하지 않고 코드로 보낸다
    if mode == "chair" and turn.event == "message" and used[-1:] == ["basis"] and not asks(turn.text):
        return write()  # 근거 질문에 평서로 답했다: 다시 판정하지 않고 코드로 적게 한다. 물음 꼴이면 아래에서 판정으로 가른다
    if turn.event == "message" and empty_answer(turn.text):
        return hinted(HARD_LEAD if hard(turn.text) else "")  # 내용 없는 답: 모델이 짓지 않는다. 다음 저장 힌트가 한 칸 더 작은 질문이다
    # 확인 질문(verify)에 답했다. 처음 생각은 이미 맞았다: 그 답(예시를 따라간 값)을 빈칸 값으로 다시 판정하지 않고 코드로 적게 한다.
    # 그 사이에 낱말의 뜻을 물었으면(term) 그 차례는 건너뛰고 본다(뜻을 물은 뒤 코드로 적는 길을 놓쳤다)
    if turn.event == "message" and [m for m in used if m != "term"][-1:] == ["verify"] and not asks(turn.text):
        return write()
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
            if not ok and retry.saved and not plain:
                return MovePlan("done", index, False, retry.lead, retry.saved, way=retry.way)
            return MovePlan("done", index, False, saved=FOUND_OK if ok else lead.strip(), fact=True)
        if plain:
            return MovePlan(LADDER[mode][min(turn.hints_seen, 2)], index, False, saved=lead.strip(), fact=True)
        # 저장 힌트가 없으면 못 해낸 첫 신호를 겨눠 짓는다(빠진 것과 다른 것을 물었다)
        return advance() if ok else hinted(lead, signal_text(blocks[index], verdict.miss if verdict else None))
    if ok and turn.event == "message" and asks(turn.text) and "verify" not in used:
        # 맞는 생각을 물음으로 냈다('range로 돌려야 하나요?'). 코드로 적으라는 고정 말은 물음에 답하지 않아 되풀이로 들렸다.
        # 맞다고 말하지 않고(답을 먼저 말하지 않는다) 그 생각을 스스로 확인할 질문을 모델이 짓는다. 말로 맞힌 생각에는 그대로 WRITE_TIP.
        # 확인 질문은 블록에 한 번만: 다시 물으면 코드로 적게 한다(확인 질문이 끝없이 이어졌다)
        return MovePlan("verify", index, False)
    if ok:
        # 근거 질문은 문항에 한 번, 생각할 거리가 있는 블록(반복·조건·분기)에서만 한다.
        # '답 담을 리스트' 같은 변수 블록마다 근거를 물으니 초보자가 멈칫했다(같은 질문이 두 블록 연달아 나왔다)
        if (mode == "chair" and (verdict.basis or "g") == "g" and not turn.basis_asked
                and blocks[index].kind in ("loop", "condition", "branch")):
            return MovePlan("basis", index, False)
        return write()
    if mode == "chair" and verdict is not None and not verdict.malformed:  # 형식 오류는 사다리
        miss = verdict.miss
        if miss and miss >= 2:
            return MovePlan("edge", index, False, missing_signal=signal_text(blocks[index], miss))
        claim = len(re.sub(r"\s+", "", turn.text)) >= CLAIM_CHARS and not any(word in turn.text for word in CONFUSED) and not hard(turn.text)
        if claim and (used[-1] if used else None) not in ("assume", "edge"):
            return MovePlan("assume", index, False, missing_signal=signal_text(blocks[index], miss))
    return ladder()
