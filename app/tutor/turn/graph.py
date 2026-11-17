"""의자·가이드 공통 그래프.

prepare(N1) -- 오류 --> END
prepare -- message --> judge(N2) --> pick_move(N4)
prepare -- block_filled --> check_code(N3) --> pick_move
prepare -- start --> pick_move
judge는 내용 없는 짧은 말('모르겠어요', '힌트', '답 알려 주세요')을 규칙으로 먼저 가른다(모델 0회)
pick_move -- 저장 힌트·고정 말 있음 --> check_reply(N6)
pick_move -- 생성 필요(내용 있는 말, 저장 힌트 없는 옛 계획) --> speak(N5) --> check_reply --> END
"""

from langgraph.graph import END, START, StateGraph

from ..common.progress_view import active_plan, found_check
from ..common.verdict import ASIDE_RULE, TERM_RULE, ask_verdict
from ..llm import llm, model_name
from ..state import MainState, MovePlan, Verdict
from .code_check import check_code
from .context import prepare
from ..common.talk_rules import OWN_WAY, WITHDRAWN, rename_note
from .moves import found_tip, pick_move, rule_verdict
from .talk import checked_reply, clean_text, speak_messages

STEPS = {"N1": "prepare", "N2": "judge", "N3": "check_code", "N4": "pick_move", "N5": "speak", "N6": "check_reply"}


def turn_graph(mode: str, judge_messages, judge_rule: str, system: str, steps: dict):
    speak_task = f"{mode}.{'ask' if mode == 'chair' else 'lead'}"

    def judge(state: MainState) -> dict:
        got = rule_verdict(state["request"].text or "")
        if got is not None:
            return {"verdict": got}
        got = ask_verdict(judge_messages(state), judge_rule + ASIDE_RULE + TERM_RULE, f"{mode}.judge")
        if got is None:  # 형식 오류는 N으로 진행한다
            return {"verdict": Verdict(False, malformed=True)}
        if mode == "chair" and got.basis is None:
            got.basis = "g"
        return {"verdict": got}

    def code(state: MainState, config) -> dict:
        return check_code(state, f"{mode}.check_code", (config or {}).get("configurable", {}).get("check"))

    def choose(state: MainState) -> dict:
        replanned = state.get("replanned")
        verdict = Verdict(False) if replanned == "rejected" else state.get("verdict")  # 그 방법으로는 안 풀린다: 못 찾음으로 잇는다
        move = pick_move(mode, active_plan(state), state["turn"], verdict, allow_follow=replanned is None, found=found_check(state) is not None,
                         language=state["ctx"].language)
        if move.move == "replan" and state["turn"].event != "replan":
            return {"move": move, "follow": state["turn"].text, "result": {"replan": True}}  # 메인 그래프가 A4로 보낸다
        request = state["request"]
        if request.own_way and request.skip and verdict is not None and verdict.ok and not verdict.ran:  # 넘어가기 판정 그대로('확인 전'), 다음 블록 말 대신 고정 말
            return {"move": MovePlan("done", state["turn"].index, True, saved=OWN_WAY)}
        return {"move": move}

    def speak(state: MainState) -> dict:
        text = llm(model_name()).use(speak_messages(state, state["turn"], state["move"], system, steps), None, task=speak_task)
        return {"reply_draft": clean_text(text)}

    def check_reply(state: MainState) -> dict:
        move = state["move"]
        named = state.get("renamed") or []
        withdrawn = state.get("withdrawn") or []
        verdict, filled = state.get("verdict"), state["request"].event == "block_filled"
        unsure = filled and verdict is not None and (verdict.unsure or (verdict.ok and not verdict.ran))  # 실행이 뒷받침하지 못했다(화면이 '확인 전'으로 그 말을 보인다)
        # 통과의 단서(실행하지 못한 판단, 공개 예시로만 확인)는 말의 맨 앞에(이름 안내·다음 블록 말보다 먼저)
        said = f"{verdict.seen} " if filled and verdict is not None and verdict.ok and verdict.seen else ""
        extra = {"renamed": named, **({"withdrawn": withdrawn} if withdrawn else {}), **({"unsure": True} if unsure else {})} if filled else {}
        note = rename_note(named)  # 이름만 달라 통과했다: 통과 말 뒤에 이름 안내(마침 말이면 뒤에, 아니면 다음 질문 앞에)
        if move.saved:  # 저장 힌트(계획 때 검사했다)와 고정 문구는 다시 검사하지 않는다. 4차 실제 모델 확인: 힌트 속 import 줄이 '참고 코드'에 걸려 대체 질문이 나갔다
            text = move.lead + move.saved
            reply = f"{text} {note}" if note and move.move == "done" else (f"{note} " if note else "") + text
        else:
            text, _ = checked_reply(state, move, state.get("reply_draft") or "")
            reply = (f"{note} " if note else "") + move.lead + text
        if withdrawn:
            reply = f"{reply} {WITHDRAWN.format(n=len(withdrawn))}"
        boxed = {"boxed": True} if filled and verdict is not None and "```" in verdict.seen else {}  # 실행에서 본 여러 줄 출력을 엔진이 글상자로 넣었다(모델의 말은 위에서 펜스를 거른다)
        tip = found_tip(mode, state["turn"], move)
        found = {"found": tip} if tip else {}  # 저장이 찾은 블록의 말로 따로 남긴다
        return {"result": {"reply": said + reply, "advance": move.advance, "move": move.move, **extra, **boxed, **found}}

    def after_prepare(state: MainState) -> str:
        if state.get("error"):
            return "end"
        turn = state["turn"]
        if state.get("replanned"):
            return "pick_move"  # 다시 짜기를 거쳐 돌아왔다. 판정은 이미 했다
        if state["request"].event == "message" and (
            (mode == "chair" and turn.moves_used[-1:] == ["basis"])
            or (turn.index == len(active_plan(state).blocks) - 1 and any(m in turn.moves_used for m in ("recap", "run", "done")))
        ):
            return "pick_move"  # 근거 질문·정리 질문의 답은 판정하지 않는다(모델 0회)
        return {"message": "judge", "block_filled": "check_code"}.get(state["request"].event or "", "pick_move")

    def after_pick(state: MainState) -> str:
        if (state.get("result") or {}).get("replan"):
            return "end"
        return "check_reply" if state["move"].saved else "speak"

    g = StateGraph(MainState)
    g.add_node("prepare", prepare)
    g.add_node("judge", judge)
    g.add_node("check_code", code)
    g.add_node("pick_move", choose)
    g.add_node("speak", speak)
    g.add_node("check_reply", check_reply)
    g.add_edge(START, "prepare")
    g.add_conditional_edges("prepare", after_prepare, {"end": END, "judge": "judge", "check_code": "check_code", "pick_move": "pick_move"})
    g.add_edge("judge", "pick_move")
    g.add_edge("check_code", "pick_move")
    # 저장 힌트와 고정 말은 바로 검사로, 나머지는 생성
    g.add_conditional_edges("pick_move", after_pick, {"check_reply": "check_reply", "speak": "speak", "end": END})
    g.add_edge("speak", "check_reply")
    g.add_edge("check_reply", END)
    return g.compile()
