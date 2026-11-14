"""A12 노드. N1 collect, N2 save, N3 respond."""

import sqlite3
from dataclasses import replace

from ..common.progress_view import current_index
from ..context.nodes import store_of
from ..state import ChatMessage, FollowupThread, MainState, fail
from ..store import now
from .respond import body_for, feedback_body


def _row(mode, thread, role, text, block_index, quote_id, move=None) -> dict:
    return {"mode": mode, "thread": thread, "role": role, "text": text, "block_index": block_index,
            "quote_id": quote_id, "move": move, "at": now()}


def collect(state: MainState) -> dict:
    """N1 저장할 것 모으기."""
    request, ctx, result = state["request"], state["ctx"], state.get("result") or {}
    rows = []
    if request.kind == "turn":
        mode = request.mode or "chair"
        user = request.text if request.event == "message" else request.code if request.event == "block_filled" and not request.quiet else ""
        if user:
            rows.append(_row(mode, "main", "user", user, current_index(state), None))
        move = state.get("move")
        rows.append(_row(mode, "main", "service", result.get("reply", ""), move.target if move else None, None, result.get("move")))
    elif request.kind == "followup":
        mode, thread = request.mode or "chair", f"quote:{request.quote_id}"
        rows += [_row(mode, thread, "user", request.text or "", None, request.quote_id),
                 _row(mode, thread, "service", result.get("reply", ""), None, request.quote_id, "followup")]
    elif request.kind == "debug":
        if (request.text or "").strip():
            rows.append(_row("chair", "debug", "user", request.text.strip(), None, None))
        rows.append(_row("chair", "debug", "service", result.get("reply", ""), None, None, result.get("move")))
    fact = state.get("abstract")
    changes = {
        "debug_state": state.get("debug_state"),
        "fact": None if fact is None else {"spec": fact.spec, "patterns": list(fact.patterns), "skills": list(fact.skills), "size": fact.size,
                                           "level": fact.level, "tags": list(fact.tags)},
        "plan": state.get("plan") or ctx.plan,
        "new_plan": state.get("plan") is not None,
        "open_count": state["open_count"],
        # 계획이 바뀌면 예전 해설은 버린다(블록이 달라졌다)
        "explain": result.get("explain") if request.kind == "explain" else (None if state.get("plan") is not None else ctx.explain),
        "messages": rows,
        "feedback": feedback_body(result) if request.kind == "feedback" else None,
        "block_check": [item for item in [state.get("block_check"), *(state.get("block_fixes") or [])] if item is not None],
        "solution": state.get("solution"),
    }
    return {"changes": changes}


def save(state: MainState, config) -> dict:
    """N2 트랜잭션 저장. 실패하면 되돌리고 오류."""
    c = state["changes"]
    try:
        store_of(config).save_success(
            state["ctx"], c["plan"], c["open_count"], c["explain"], c["messages"], c["feedback"],
            new_plan=c["new_plan"], block_check=c["block_check"], debug_state=c["debug_state"], fact=c["fact"], solution=c.get("solution"),
            own_solution=c["new_plan"] and c["plan"] is not None and c["plan"].strategy == "keep_flow",  # 사용자 코드·사용자 방법을 따른 계획의 가이드
        )
    except sqlite3.Error:
        return fail("store_failed", "저장하지 못했어요. 앱을 닫았다가 다시 열어 주세요.")
    index = (config or {}).get("configurable", {}).get("index")
    if index is not None and c["new_plan"] and c["plan"] is not None:
        fact = c["fact"] or {"spec": state["ctx"].spec, "patterns": list(state["ctx"].patterns)}
        if fact["spec"]:
            try:  # 색인은 덤이다(진실은 SQLite). 실패해도 저장은 끝났다
                index.put(state["ctx"].problem_id, fact["spec"], " → ".join(b.name for b in c["plan"].blocks),
                          {"algorithm": c["plan"].algorithm, "patterns": fact["patterns"], "title": state["ctx"].title})
            except Exception:  # noqa: BLE001
                pass
    return {}


def _merged(state: MainState):
    """다시 읽기에 실패했을 때: 저장할 변경을 문맥에 얹어 같은 모양을 만든다(이미 커밋됐으므로 오류로 만들지 않는다)."""
    ctx, c, request = state["ctx"], state["changes"], state["request"]
    new = [ChatMessage(id="", role=r["role"], text=r["text"], at=r["at"], block_index=r["block_index"], quote_id=r["quote_id"], move=r["move"]) for r in c["messages"]]
    chair, guide, followups = list(ctx.chair), list(ctx.guide), list(ctx.followups)
    if request.kind == "turn":
        (guide if request.mode == "guide" else chair).extend(new)
    elif request.kind == "followup":
        old = next((t for t in followups if t.quote_id == request.quote_id), None)
        followups = [t for t in followups if t is not old] + [FollowupThread(request.quote_id, (old.messages if old else []) + new)]
    if request.kind == "debug":
        return replace(ctx, debug=list(ctx.debug) + new, debug_state=c["debug_state"])
    return replace(ctx, plan=c["plan"], open_count=c["open_count"], explain=c["explain"], chair=chair, guide=guide, followups=followups)


def respond(state: MainState, config) -> dict:
    """N3 응답 만들기."""
    try:
        ctx = store_of(config).load(state["ctx"].problem_id) or _merged(state)
    except sqlite3.Error:
        ctx = _merged(state)
    return {"response": {"status": 200, "body": body_for(state["request"], state.get("result") or {}, ctx)}}
