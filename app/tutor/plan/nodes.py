"""A4 노드. abstract → assess → pick_strategy → solve → recall → draft_blocks → check_blocks → clean_hints. 채점·전략은 A10과 같이 쓴다.

풀이 가이드(solve)가 먼저다: 문제 글만 보고 정답 풀이를 만들어 채점기로 확인하고, 블록은 그 코드를 순서대로 나눈다.
지난 문항에서 불러온 것은 풀이를 정하지 않는다. 사용자가 풀어 본 같은 구조 문항 하나를 '떠올리게 하는 한 줄'로만 남긴다(recall).
"""

import os
import sys
from dataclasses import replace

from ..common.assess import assess_node, pick_strategy_node
from ..common.solution import entry_params, frame_flags, solution_of
from ..common.talk_prompts import weak_pitfalls
from ..common.talk_rules import UNRUN_FIX, unrun_why
from ..debug.rules import error_tail, symptom
from ..knowledge.ontology import SKILLS, known_patterns, known_skills, known_techniques, pattern_context, size_rule
from ..llm import LlmError, llm, model_name, themes
from ..output_check.nodes import strip_fence
from ..state import Abstract, BlockPlan, CaseMaker, DraftedBlocks, ErrorInfo, MainState, MendedHints, Solution, Solved, Written
from .prompts import abstract_text, brute_messages, draft_messages, gate_messages, hint_messages, maker_messages, solve_messages
from .rules import check_blocks as check_rule
from .rules import clean_blocks, cut_by_rule, hint_faults


def direct_code(state: MainState) -> str:
    return state["ctx"].direct_code or ""


def abstract(state: MainState) -> dict:
    """N1 문항 뼈대 뽑기: 이야기를 걷어 낸 명세와 온톨로지 패턴. 이미 있으면 다시 뽑지 않는다. 실패해도 계획은 만든다."""
    ctx = state["ctx"]
    if ctx.spec:
        return {}
    try:
        got: Abstract = llm(model_name()).use(abstract_text(ctx.problem_text), Abstract, task="plan.abstract")
    except LlmError:
        return {}
    return {"abstract": Abstract(spec=got.spec.strip(), patterns=known_patterns(got.patterns), skills=known_skills(got.skills)[:4],
                                 size=got.size if isinstance(got.size, int) and got.size > 0 else 0,
                                 level=got.level if 1 <= got.level <= 5 else 0, tags=known_techniques(got.tags)[:4])}


def facts(state: MainState):
    """문항 뼈대(명세, 패턴, 구현 기술, 입력 크기). 이번 요청에서 뽑았으면 그것, 아니면 저장된 것."""
    return state.get("abstract") or state["ctx"]


SOLVE_TRIES = 3  # 처음 한 번 + 채점에서 틀리거나 머리가 시작 코드와 다르면 두 번 더
HEAD_DIFFERS = "진입 함수 머리가 시작 코드와 다름"  # 끝내 다르면 예시를 통과하지 못한 가이드로 둔다(채점 결과 자리에 적힌다)
# 풀이 코드를 고쳐 다시 쓸 수 있는 결과(사용자 코드 탓의 채점 + 진입 함수 없음 + 머리 불일치). 그 밖(도구·케이스 없음, 인자 형 미지원)은 다시 써도 채점되지 않는다
REWRITABLE = ("failed", "timeout", "compile_error", "runtime_error", "entry_missing", HEAD_DIFFERS)


def verified_by(report: dict | None) -> bool | None:
    """채점 결과로 본 풀이 가이드의 확인: 통과(True), 통과하지 못함(False), 채점하지 못함(None. 도구·케이스가 없거나 인자 형을 다루지 못함)."""
    status = (report or {}).get("status")
    return True if status == "passed" else False if status in REWRITABLE else None


def head_differs(state: MainState, code: str) -> bool:
    """함수 방식에서 시작 코드에 진입 함수 머리가 있는데, 가이드 코드의 머리가 인자 이름·차례가 다르거나 없다.
    시작 코드대로 쓴 블록이 계획 코드와 이어지면 이름이 어긋나 NameError였다."""
    ctx = state["ctx"]
    want = entry_params(ctx.starter, ctx.language) if ctx.mode == "function" else None
    return want is not None and entry_params(code, ctx.language) != want


def solve(state: MainState, config) -> dict:
    """풀이 가이드: 문제 글만 보고 풀이 방향·단계·정답 코드를 만들고, 채점기가 있으면 테스트 케이스로 확인한다.

    정석 가이드는 문제마다 하나다: 이미 있으면 다시 만들지 않고 그것으로 블록을 짠다(여러 번 풀어도 같은 방향).
    사용자 코드나 사용자가 말한 방법을 따를 때만 그 방법의 가이드를 따로 만든다(정석 가이드는 덮어쓰지 않는다).
    모델이 실패하면 가이드 없이 간다(블록은 예전 방식으로 짠다).
    사용자 방법 따르기에서 그 방법으로 못 풀면(followed=false, 또는 채점 실패) 지금 계획을 지킨다.
    """
    ctx, strategy = state["ctx"], state.get("strategy") or "fresh"
    if ctx.canonical is not None and strategy in ("fresh", "canonical"):
        return {"solution": ctx.canonical}
    if os.environ.get("ALGOBLOCK_BENCH_NO_GUIDE"):  # 측정용: 가이드 없이(예전 방식) 블록을 짠다
        return {}
    check = (config or {}).get("configurable", {}).get("check")
    given = (config or {}).get("configurable", {}).get("given")
    cross = (config or {}).get("configurable", {}).get("cross")
    fixed = given(ctx.problem_id, ctx.language) if given is not None and strategy in ("fresh", "canonical") else None
    if fixed and (fixed.get("code") or "").strip():
        return _given_guide(state, fixed, check)
    retry, got, report = "", None, None
    for _ in range(SOLVE_TRIES):
        try:
            got: Solved = llm(model_name()).use(solve_messages(state, retry), Solved, task="plan.solve")
        except LlmError:
            return {}
        code = strip_fence(got.code or "").strip("\n")
        got = replace(got, code=code)
        if strategy == "follow" and not got.followed:
            return {"replanned": "rejected", "result": None}
        if head_differs(state, code):  # 실행하기 전에 규칙으로 본다
            retry, report = f"코드:\n{code}\n진입 함수 머리가 시작 코드와 다르다. 시작 코드의 머리(함수 이름, 인자 이름과 차례)를 그대로 쓴다.", {"status": HEAD_DIFFERS}
            continue
        report = check(ctx.problem_id, code) if check is not None and code.strip() else None
        if report is None or report.get("status") not in REWRITABLE:  # 통과했거나, 채점하지 못했다(케이스·채점기·도구가 없음. 다시 써도 같다)
            break
        retry = "\n".join(part for part in (f"코드:\n{code}", f"채점 결과: {report.get('status')}", symptom(report), error_tail(report)) if part)
    else:
        if strategy == "follow":
            return {"replanned": "rejected", "result": None}  # 사용자 방법으로는 통과하는 코드를 못 썼다
    if not got.code.strip() or not got.approach.strip():
        return {}
    if cross is not None and check is not None and strategy in ("fresh", "canonical") and cross.mode(ctx.problem_id):
        got = cross_check(state, got, verified_by(report), report, check, cross)  # 정석 가이드만 실행으로 대조한다(사용자 코드·방법을 따른 가이드는 하지 않는다)
    return {"solution": Solution(got.approach.strip(), [step.strip() for step in got.steps if step.strip()], got.code, verified_by(report),
                                 [clue.strip() for clue in got.clues if clue.strip()]), **guide_labels(state, got)}


def guide_labels(state: MainState, got: Solved) -> dict:
    """이번에 뽑은 뼈대의 태그·단계를 정석 가이드가 코드로 정한 것으로 바꾼다. 뼈대는 글만 보고 정해 문제 글의 분류 표시에 끌렸다.
    가이드가 주지 않은(목록 밖 낱말뿐이거나 범위 밖) 것은 뼈대 그대로 둔다. 사용자 코드·방법을 따른 가이드는 바꾸지 않는다."""
    fact = state.get("abstract")
    if fact is None or (state.get("strategy") or "fresh") not in ("fresh", "canonical"):
        return {}
    tags = known_techniques(got.tags)[:4]
    return {"abstract": replace(fact, tags=tags or fact.tags, level=got.level if 1 <= got.level <= 5 else fact.level)}


EXTRA_CALLS = 5  # 대조가 문제 하나의 준비에 더 쓰는 모델 호출 상한(단순 풀이, 생성기, 다시 풀기: 가운데 급 1회 + 큰 급 1회)
VERIFIED = {"same": "all", "differ": "none"}  # 대조 결과 → 문제의 검증: 예시와 대조 모두 통과, 검증하지 못함. 그 밖(대조하지 못함)은 예시만 통과(examples)


def cross_check(state: MainState, got: Solved, passed: bool | None, report: dict | None, check, cross) -> Solved:
    """모델의 풀이는 실행으로 확인한 것만 믿는다. 공개 예시를 통과한 정답 풀이를, 정의 그대로 옮긴 단순 풀이와
    생성기가 만든 작은·경계 입력에서 대조한다. 실행은 모두 cross.run(채점기 프로세스)이 하고, 맞으면 그 입력이 숨은 케이스가 된다.
    다르면 그 입력을 보여 주며 가운데 급으로 한 번, 그래도 다르면 큰 급으로 한 번 다시 푼다(다시 푼 코드도 공개 예시를 통과해야 쓴다).
    결과(검증, 쓴 호출 수와 급, 확인이 필요한 곳)는 cross.done으로 남긴다. 고른 풀이를 돌려준다."""
    pid = state["ctx"].problem_id
    verdict = {"verified": "none", "calls": 0, "tiers": ["middle"], "doubts": [], "why": "", "hidden": 0, "efficiency": 0}
    if passed is None:  # 채점하지 못했다: 풀이가 틀렸다고 말하지 않는다
        status = (report or {}).get("status") or "no_cases"
        verdict.update(why=f"튜터의 풀이를 확인하지 못했어요. {unrun_why(status)}.{UNRUN_FIX.get(status, '')}")
        cross.done(pid, verdict)
        return got
    if not passed:  # 사용자가 넣은 기대 결과를 믿는다: 끝내 맞지 않은 예시는 문제를 잘못 읽었을 수 있다
        verdict.update(why="AI가 쓴 풀이가 공개 예시를 통과하지 못했어요. 예시의 기대 결과가 맞는지 확인해 주세요.", doubts=[
            {"where": f"예시 {row['id']}", "note": "기대 결과와 풀이가 맞지 않음"} for row in (report or {}).get("cases") or []
            if row.get("kind", "example") == "example" and row.get("status") != "passed"])
        cross.done(pid, verdict)
        return got
    mode, text = cross.mode(pid), state["ctx"].problem_text
    try:
        brute: Written = llm(model_name()).use(brute_messages(text, mode), Written, task="plan.brute")
        verdict["calls"] += 1
        maker: CaseMaker = llm(model_name()).use(maker_messages(text, mode), CaseMaker, task="plan.cases")
        verdict["calls"] += 1
    except LlmError:
        verdict.update(verified="examples", why="검증용 풀이를 받지 못해 예시로만 확인했어요.")
        cross.done(pid, verdict)
        return got
    brute_code, maker_code = strip_fence(brute.code or ""), strip_fence(maker.code or "")
    for tier in ("middle", "large", ""):
        found = cross.run(pid, got.code, brute_code, maker_code, maker.bounds)
        if found["status"] != "differ" or not tier or verdict["calls"] >= EXTRA_CALLS:
            break
        retry = "\n".join([f"코드:\n{got.code}", "문제 정의를 그대로 옮긴 느린 풀이와 결과가 다른 입력이 있다(느린 풀이가 틀렸을 수도 있으니 문제 글로 다시 따진다).",
                           f"입력: {found.get('input')}", f"이 코드의 결과: {found.get('got')}", f"느린 풀이의 결과: {found.get('want')}"])
        try:
            again: Solved = llm(model_name() if tier == "middle" else themes.model_of("large")).use(solve_messages(state, retry), Solved, task="plan.solve")
        except LlmError:
            break
        verdict["calls"] += 1
        verdict["tiers"].append(tier)
        code = strip_fence(again.code or "").strip("\n")
        if code.strip() and again.approach.strip() and not head_differs(state, code) and (check(pid, code) or {}).get("status") == "passed":
            got = replace(again, code=code)
    verdict.update(verified=VERIFIED.get(found["status"], "examples"), why=found.get("why") or "",
                   hidden=found.get("hidden") or 0, efficiency=found.get("efficiency") or 0)
    if found["status"] == "differ":
        verdict["why"] = verdict["why"] or ("가장 큰 입력에서 제한 시간 안에 끝나지 않았어요." if found.get("slow")
                                            else f"다른 방법으로 푼 결과와 다른 입력이 있어요: {str(found.get('input'))[:200]}")
    cross.done(pid, verdict)
    return got


def _given_guide(state: MainState, fixed: dict, check) -> dict:
    """정답 코드가 정해져 있다(기본 문제의 검증된 풀이): 코드는 그대로 쓰고, 단서·방향·단계가 같이 오지 않았으면 그것만 모델이 쓴다.
    채점기가 있으면 그 코드를 다시 확인한다. 모델이 실패하면 가이드 없이 간다."""
    ctx = state["ctx"]
    code = fixed["code"].strip("\n")
    if not (fixed.get("approach") or "").strip():
        try:
            got: Solved = llm(model_name()).use(solve_messages(state, given=code), Solved, task="plan.solve")
        except LlmError:
            return {}
        fixed = {"clues": got.clues, "approach": got.approach, "steps": got.steps}
        if not fixed["approach"].strip():
            return {}
    report = check(ctx.problem_id, code) if check is not None else None
    return {"solution": Solution(fixed["approach"].strip(), [step.strip() for step in fixed.get("steps") or [] if step.strip()], code,
                                 verified_by(report), [clue.strip() for clue in fixed.get("clues") or [] if clue.strip()])}


def recall(state: MainState, config) -> dict:
    """지식 불러오기. 블록의 신호·힌트에 쓰는 참고(온톨로지의 함정 후보와 구현 기술, 이 사용자가 되풀이한 실수)와,
    사용자가 풀어 본 같은 구조 문항 한 줄(link). 지난 문항은 임베딩으로 후보 하나를 고른 뒤 모델이 같은 구조라고 판정해야 남는다."""
    ctx = state["ctx"]
    known = facts(state)
    spec, patterns = known.spec, list(known.patterns)
    lines = pattern_context(patterns)
    rule = size_rule(known.size)
    if rule:
        lines.append(f"- 입력 크기: {rule}")
    skills = [f"- 구현 기술 '{SKILLS[sid][0]}': {SKILLS[sid][1]}" for sid in known_skills(known.skills)]
    weak = weak_pitfalls(ctx)
    return {"recall": {"spec": spec, "patterns": lines, "skills": skills, "weak": weak}, "link": _link(state, config, spec, patterns)}


def _link(state: MainState, config, spec: str, patterns: list[str]) -> str:
    """사용자가 풀어 본(제출한 적 있는) 문항 가운데 같은 구조 하나. 없으면 빈 글. 실패해도 계획은 만든다."""
    ctx, guide = state["ctx"], solution_of(state)
    tried = {item["problem_id"]: item for item in ctx.library if item.get("tried") and item["flow"] and item.get("spec")}
    if not tried or not spec or guide is None:
        return ""
    index = (config or {}).get("configurable", {}).get("index")
    order: list[str] = []
    if index is not None:
        try:
            order = [hit["problem_id"] for hit in index.similar(spec, exclude=ctx.problem_id, limit=5, patterns=patterns)]
        except Exception:  # noqa: BLE001 - 벡터 찾기는 덤이다
            order = []
    order += sorted((pid for pid, item in tried.items() if set(item["patterns"]) & set(patterns)),
                    key=lambda pid: -len(set(tried[pid]["patterns"]) & set(patterns)))
    picked = next((tried[pid] for pid in order if pid in tried), None)
    if picked is None:
        return ""
    try:
        answer = llm(model_name()).use(gate_messages(spec, guide.approach, picked), None, task="plan.gate", max_tokens=16)
    except LlmError:
        return ""
    return f"{picked['title'] or '전에 푼 문제'}: {picked['flow']}" if (answer or "").strip().upper().startswith("Y") else ""


assess = assess_node("plan.assess", direct_code)
pick_strategy = pick_strategy_node(direct_code)


def draft_blocks(state: MainState) -> dict:
    """블록 초안. 풀이 가이드가 있으면 블록은 그 코드의 줄 구간이다: 구간이 코드를 빠짐없이 순서대로 나누는지 보고(작은 어긋남은 규칙으로 고친다),
    아니면 한 번 다시 받는다. 그래도 쓸 수 없으면 규칙으로 자르고 이름·목표·질문만 모델에게 받는다(rule_cut)."""
    guide = solution_of(state)
    drafted: DraftedBlocks = llm(model_name()).use(draft_messages(state), DraftedBlocks, task="plan.draft_blocks")
    if guide is None:
        return {"draft": replace(drafted, blocks=mend_hints(state, list(drafted.blocks)))}
    language = state["ctx"].language
    program = state["ctx"].mode == "program"
    for again in (True, False):
        cut = cut_by_lines(drafted.blocks, guide.code, language, program)
        if cut is not None:
            return {"draft": replace(drafted, blocks=mend_hints(state, cut))}
        print(f"[plan.draft_blocks] 줄 구간을 쓸 수 없음: {[list(b.lines) for b in drafted.blocks]} / 코드 {len(guide.code.splitlines())}줄", file=sys.stderr)
        if again:
            drafted = llm(model_name()).use(draft_messages(state), DraftedBlocks, task="plan.draft_blocks")
    # Java 풀이에서 모델이 두 번 다 마지막 줄('}')을 빠뜨려 준비 전체가 실패했다. 마지막 길로 규칙으로 자른다
    blocks = cut_by_rule(guide.code, language, program)
    if not blocks:
        return {"error": ErrorInfo("invalid_output", "블록이 풀이 코드를 빠짐없이 나누지 않았습니다."), "draft": None}
    return {"draft": replace(drafted, blocks=mend_hints(state, blocks, named=True)), "rule_cut": True}


def mend_hints(state: MainState, blocks: list, named: bool = False) -> list:
    """원칙을 어겨 버려질 질문을 그 블록만 한 번 다시 받는다(다시 풀어도 같은 질문으로 시작하게).
    다시 받은 것도 어기면 clean_hints가 비우고, 그 블록은 대화 때 모델이 질문을 만든다.
    named: 규칙으로 자른 블록이다. 모든 블록의 이름·목표·신호·질문을 한 번에 받는다(실패하면 종류에서 만든 일반 문구 그대로)."""
    faults = {b.id: ["이름·목표·신호·질문이 없음"] for b in blocks} if named else hint_faults(blocks, state["ctx"].problem_text)
    if not faults:
        return blocks
    try:
        got: MendedHints = llm(model_name()).use(hint_messages(state, blocks, faults, named), MendedHints, task="plan.hints")
    except LlmError:
        return blocks
    new = {row.id: row for row in got.blocks if row.id in faults}

    def mended(block):
        row = new.get(block.id)
        if row is None:
            return block
        if not named:
            return replace(block, hints=list(row.hints))
        return replace(block, name=row.name.strip() or block.name, goal=row.goal.strip() or block.goal,
                       checks=[c for c in row.checks if c.strip()] or block.checks, hints=list(row.hints))

    return [mended(block) for block in blocks]


def cut_by_lines(blocks, code: str, language: str = "python", program: bool = False):
    """블록의 lines 구간으로 가이드 코드를 잘라 reference에 넣는다. 구간이 1번 줄부터 끝 줄까지 이어지지 않으면 None.
    작은 어긋남은 고친다: 처음·끝에서 빠뜨린 틀 줄·빈 줄, 이웃 블록 사이의 한 줄 빈틈·한 줄 겹침."""
    rows = code.splitlines()
    spans = [list(block.lines) for block in blocks]
    if not spans or any(len(span) != 2 for span in spans):
        return None
    skip = frame_flags(rows, language, program)
    if 1 < spans[0][0] <= len(rows) and all(skip[: spans[0][0] - 1]):
        spans[0][0] = 1
    if 0 < spans[-1][1] < len(rows) and all(skip[spans[-1][1]:]):
        spans[-1][1] = len(rows)
    for before, after in zip(spans, spans[1:]):
        gap = after[0] - before[1] - 1
        if gap == -1:
            after[0] += 1  # 한 줄 겹침: 뒤 블록이 양보한다
        elif gap == 1:
            missing = rows[before[1]].rstrip() if 0 <= before[1] < len(rows) else ""
            if missing.endswith(("{", ":")):
                after[0] -= 1  # 여는 줄(반복·조건 머리)은 뒤 블록으로
            else:
                before[1] += 1  # 닫는 괄호 같은 줄은 앞 블록으로
    at, out = 1, []
    for block, span in zip(blocks, spans):
        if span[0] != at or span[1] < span[0] or span[1] > len(rows):
            return None
        out.append(replace(block, lines=span, reference="\n".join(rows[span[0] - 1 : span[1]])))
        at = span[1] + 1
    return out if at == len(rows) + 1 else None


def check_blocks(state: MainState) -> dict:
    if state.get("error"):
        return {}
    drafted: DraftedBlocks = state["draft"]
    error = check_rule(list(drafted.blocks), drafted.algorithm)
    if state.get("strategy") == "follow" and (error or not drafted.followed):
        return {"replanned": "rejected", "draft": None, "result": None}  # 사용자 방법으로는 못 짰다: 지금 계획을 지킨다
    return {"error": error, "draft": None} if error else {}


def clean_hints(state: MainState) -> dict:
    if state.get("replanned") == "rejected":
        return {}
    drafted: DraftedBlocks = state["draft"]
    follow = state.get("strategy") == "follow"
    plan = BlockPlan(
        strategy="rule_cut" if state.get("rule_cut") else "keep_flow" if follow else (state.get("strategy") or "fresh"),
        score=state.get("score"),
        blocks=clean_blocks(list(drafted.blocks), state["ctx"].problem_text, state["ctx"].language),
        algorithm=drafted.algorithm,
        out_of_scope=bool(drafted.out_of_scope),
        link=state.get("link") or "",
    )
    extra = {"replanned": "followed", "result": None} if follow else {}
    return {"plan": plan, "draft": None, "open_count": 1, **extra}
