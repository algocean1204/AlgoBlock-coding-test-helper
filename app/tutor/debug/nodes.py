"""디버그 노드: gather → locate/judge → pick_step → speak → check_reply(graph.py)."""

from ..common.talk_rules import BACK_LEAD, agree_opening, asks_ignored, banned_in, quotes_ok, repair, unsaid_credit, without_code
from ..common.verdict import ASIDE_RULE, FOUND_RULE, ask_verdict
from ..knowledge.ontology import PITFALLS, pitfall_candidates, pitfall_lines
from ..llm import llm, model_name
from ..state import DebugState, Diagnosis, MainState
from . import rules
from ..turn.moves import rule_verdict
from .prompts import found_messages, locate_messages, speak_messages

LEADS = {"A": rules.ANSWER_LEAD, "O": BACK_LEAD}  # 답을 달라는 말, 무관한 말에 엔진이 붙이는 앞말


def gather(state: MainState) -> dict:
    """gather: 실패 요약과 지난 진단. 같은 코드면 진단을 다시 쓰고, 새 코드면 처음부터."""
    ctx, req = state["ctx"], state["request"]
    digest = rules.code_hash(req.code or "")
    saved = ctx.debug_state if ctx.debug_state is not None and ctx.debug_state.code_hash == digest else None
    said = ctx.debug if saved is not None else []
    service = [m for m in said if m.role == "service"]
    draft = {
        "hash": digest,
        "cached": saved is not None,
        "previous": None if saved is None else saved.step,
        "recent": [f"{'튜터' if m.role == 'service' else '사용자'}: {m.text}" for m in said][-4:],
        "last_question": service[-1].text if service else "없음",
        "candidates": pitfall_candidates(ctx.patterns, [pid for pid, _ in ctx.frequent_pitfalls], ctx.language),
        # 이 문제·언어의 증명된 언어 함정 가운데 이 실패와 맞을 수 있는 것(모델 없이 거른다). 같은 코드면 다시 고르지 않는다
        "traps": [] if saved is not None else rules.trap_candidates(ctx.traps, req.report or {}, req.code or ""),
        "found": False,
    }
    if saved is not None:
        draft.update(kind=saved.kind, line=saved.line, cause=saved.cause, fixed_line=saved.fixed_line, pitfall=saved.pitfall, trap=saved.trap)
    return {"draft": draft}


def locate(state: MainState) -> dict:
    """locate: 진단(보이지 않음). 채점 결과로 알 수 있는 것(문법 오류, 오류 줄)은 모델 답보다 먼저다."""
    draft, report = dict(state["draft"]), state["request"].report or {}
    messages = locate_messages(state)
    hint = []
    if draft["candidates"]:
        hint += ["pitfall: 아래 초보자 함정 목록(참고용 분류표)에서 이 원인에 해당하는 id 하나. 맞는 것이 없으면 빈 글로 둔다(억지로 고르지 않는다). 진단은 코드와 채점 결과로 한다.",
                 *pitfall_lines(draft["candidates"], state["ctx"].language)]
    traps = draft.get("traps") or []
    if traps:  # 실패마다 달라지는 글이라 캐시 앞부분 뒤(메시지 끝)에 붙는다
        hint += ["trap: 아래는 이 문제와 언어에서 실제로 틀리는 것이 확인된 실수다. 이 실패의 원인이 그 가운데 하나와 같을 때만 그 id를 적는다. 아니면 빈 글로 둔다(억지로 고르지 않는다).",
                 *(f"- {trap['id']}: {trap['what']}" for trap in traps)]
    if hint:
        messages[-1] = {**messages[-1], "content": messages[-1]["content"] + "\n" + "\n".join(hint)}
    got: Diagnosis = llm(model_name()).use(messages, Diagnosis, task="debug.locate")
    total = len((state["request"].code or "").splitlines())
    kind = rules.kind_hint(report)  # 종류는 채점 결과가 정한다(오류 글이 있으면 문법·실행, 없으면 답이 틀림)
    reported = rules.error_line(report) if kind != "logic" else None  # 오류가 난 줄은 채점 결과가 안다. 모델이 짐작한 줄보다 먼저다
    line = reported if reported and reported <= total else got.line if 1 <= got.line <= total else 0
    draft.update(kind=kind, line=line, cause=got.cause.strip(), fixed_line=got.fixed_line.rstrip(),  # 들여쓰기가 고침일 수 있어 앞 공백은 둔다
                 pitfall=got.pitfall if got.pitfall in PITFALLS else "", trap=got.trap if rules.trap_of(traps, got.trap) else "",  # 내놓은 후보에 없는 id는 버린다
                 opening=(got.opening or "").strip().strip('"“”'))
    return {"draft": draft}


def judge(state: MainState) -> dict:
    """judge: 사용자가 원인을 짚었는가. 형식이 틀리면 못 짚은 것으로 본다.
    답을 달라는 말(A)과 무관한 말(O)은 의자처럼 가른다: 짧은 답 요청은 규칙으로(모델 0회), 그 밖은 판정이 함께 본다."""
    got = rule_verdict(state["request"].text or "")
    if got is None or not got.aside:
        got = ask_verdict(found_messages(state), FOUND_RULE + ASIDE_RULE, "debug.judge")
    return {"draft": {**state["draft"], "found": bool(got and got.ok), "aside": got.aside if got else ""}}


def pick_step(state: MainState) -> dict:
    """pick_step: 질문 단계(규칙). 새 코드면 첫 단계, 원인을 짚었으면 마침, 아니면 한 단계 더 좁힌다."""
    draft = dict(state["draft"])
    step, name = rules.next_step(draft["kind"], draft["previous"] if draft["cached"] else None, draft["found"])
    draft.update(step=step, step_name=name)
    return {"draft": draft}


def speak(state: MainState) -> dict:
    """speak: 질문 만들기. 사용자 말 없이 시작하는 첫 질문은 진단이 함께 지은 것(opening)이다(모델을 다시 부르지 않는다). 사용자가 말했으면 그 말을 받아 모델이 쓴다."""
    draft = state["draft"]
    if opening(state):
        return {"reply_draft": draft.get("opening") or ""}
    text = llm(model_name()).use(speak_messages(state), None, task="debug.ask")
    return {"reply_draft": (text or "").strip().strip('"“”')}


def opening(state: MainState) -> bool:
    """사용자 말 없이 새 코드로 시작하는 첫 질문인가."""
    return state["draft"]["step_name"] == "symptom" and not (state["request"].text or "").strip()


def check_reply(state: MainState) -> dict:
    """check_reply: 말풍선 검사. 고친 줄이 새거나 원칙을 어기면 단계별 대체 질문.
    첫 질문은 증상(기대·실제 값, 엔진이 쓴 사실) 뒤에 진단이 지은 질문을 붙인다. 걸리면 정해진 증상 질문."""
    draft, req = state["draft"], state["request"]
    name = draft["step_name"]
    text = state.get("reply_draft") or ""
    first = opening(state)
    said = "\n".join([req.code or "", req.text or "", *draft["recent"]])
    text = repair(text, state["ctx"].problem_text, said, user=req.text or "")
    bad = (not text or "```" in text or not text.rstrip().endswith(("?", "？"))
           or banned_in(text, state["ctx"].problem_text + "\n" + said) or agree_opening(text, state["ctx"].problem_text)
           or rules.leaks_fix(text, draft["fixed_line"], req.code or "")
           # 문제 글·내 말에 없는 큰따옴표 인용("앞 사람 여분을 먼저 확인한다")이 나왔다
           or not quotes_ok(without_code(text), state["ctx"].problem_text, said, double=True)
           or unsaid_credit(text, req.text or "")  # 하지 않은 판단을 인정했다
           or asks_ignored(text, req.text or "")  # 물음이 여럿인데 하나도 받지 않았다
           # 첫 질문이 원인 줄이나 고친 줄의 조각을 알려 주면 사다리가 무너진다('4줄에서…', '네 번째 줄', 'count.get(name, 0) + 1로')
           or (first and (rules.names_line(text) or rules.leaks_piece(text, draft["fixed_line"], req.code or "")))
           # 줄 번호를 알려 주지 않는 단계에서 줄 번호를 말하면 고칠 것(고친 줄의 조각)을 함께 말하지 않는다. fix·form 단계는 문법 예를 보여 준다
           or (name not in rules.SHOWS_LINE and rules.names_line(text) and rules.leaks_piece(text, draft["fixed_line"], req.code or "")))
    if first:
        report = req.report or {}
        text = rules.symptom_question(report) if bad else f"{rules.symptom(report)} {text}"
    elif bad:
        text = rules.fallback(name, draft["line"])
    trap = rules.trap_of(state["ctx"].traps, draft.get("trap") or "")
    if trap and name == "cause" and draft["previous"] != draft["step"]:  # 원인 설명 단계에 처음 왔을 때만, 무슨 일이 일어나는지(what)만. 고치는 법(fix)은 사용자가 찾는다
        text = f"{trap['what']} {text}"
    text = LEADS.get(draft.get("aside") or "", "") + text
    record = DebugState(code_hash=draft["hash"], kind=draft["kind"], line=draft["line"], cause=draft["cause"],
                        fixed_line=draft["fixed_line"], step=draft["step"], pitfall=draft.get("pitfall") or "", trap=draft.get("trap") or "")
    line = (draft["line"] if name in rules.SHOWS_LINE and draft["line"] else None) or rules.said_line(text, req.code or "")
    return {"result": {"reply": text, "move": name, "line": line, "kind": draft["kind"]}, "debug_state": record, "draft": None}
