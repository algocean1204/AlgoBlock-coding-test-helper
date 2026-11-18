"""응답 본문. 블록은 번호·종류·이름만 내보낸다(참고 코드, 목표, 신호, 힌트는 숨김).

잠긴 블록(아직 열리지 않은 블록)의 이름은 null이다. 말풍선이 뒤 블록 이름을 말하지 않는 것과 같은 이유다(화면이 먼저 답을 보여 주지 않게).
해설은 답을 보는 모드라 이름을 모두 낸다.
"""

from ..common.solution import shown_kind
from ..state import Explain


def blocks_body(plan, open_count: int | None = None, language: str = "python") -> list[dict]:
    """open_count를 주면 그 뒤 블록 이름은 가린다. 종류는 그 블록의 코드와 맞을 때만 낸다(shown_kind)."""
    if plan is None:
        return []
    shown = len(plan.blocks) if open_count is None else open_count
    return [{"id": b.id, "kind": shown_kind(b, language), "name": b.name if i < shown else None} for i, b in enumerate(plan.blocks)]


DONE_MOVES = ("recap", "run", "close")  # 마지막 블록까지 찾은 뒤의 말


def chair_said(ctx, moves, index: int | None = None) -> bool:
    """의자의 튜터가 지금 계획에서(마지막 다시 짜기 뒤) 그 차례의 말을 했는가. index를 주면 그 블록의 말만 본다."""
    cut = max((i for i, m in enumerate(ctx.chair) if m.role == "service" and m.move == "replan"), default=0)
    return any(m.role == "service" and m.move in moves and (index is None or m.block_index == index) for m in ctx.chair[cut:])


def shown_count(ctx, mode: str | None) -> int:
    """이름을 보여 줄 블록 수. 가이드는 지금 블록까지(빈칸을 채우는 모드), 의자는 이미 찾은 블록까지(지금 블록 이름은 사용자가 찾을 답이다).
    의자에서 지금 블록을 말로 찾았거나(코드로 적으라는 말 write) 끝냈으면(마지막 블록을 내 방식으로 넘긴 done) 그 블록 이름까지 보인다."""
    if mode != "chair":
        return ctx.open_count
    named = chair_said(ctx, DONE_MOVES) or chair_said(ctx, ("write", "done"), ctx.open_count - 1)
    return ctx.open_count if named else max(ctx.open_count - 1, 0)


def messages_body(items) -> list[dict]:
    """block_index: 그 말이 겨눈 블록 번호(0부터, 없으면 null). 화면이 말 위 블록 종류 구분선을 그 블록 것으로 그린다.
    move: 튜터 말의 차례 이름(사용자 말은 null). 화면이 다음 할 일을 고른다(write면 블록 코드 확인)."""
    return [{"id": item.id, "role": item.role, "text": item.text, "at": item.at, "block_index": item.block_index,
             "move": item.move if item.role == "service" else None} for item in items]


def explain_json(explain: Explain | None):
    if explain is None:
        return None
    return {"sections": [{"title": s.title, "body": s.body} for s in explain.sections]}


def explain_body(ctx) -> dict:
    return {"explain": explain_json(ctx.explain), "blocks": blocks_body(ctx.plan, None, ctx.language), "open_count": ctx.open_count}


def feedback_body(result: dict) -> dict:
    """저장하는 피드백. 점수는 넣지 않는다."""
    return {key: result.get(key) for key in ("submission_id", "analysis", "similar_hint", "strategy", "advice")}


def framed_blocks(ctx, mode: str | None) -> list[dict]:
    """열린 블록에 저장된 확인 상태를 더한다: checked(저장된 글), stale(앞 블록이 바뀌어 '확인 전'으로 돌아갔거나 다시 확인이 실패했다).
    화면은 칸 글이 저장된 글과 다르거나 stale이면 '블록 코드 확인'을 보인다. 모으기는 서버가 한다(틀 정보는 싣지 않는다)."""
    rows = blocks_body(ctx.plan, shown_count(ctx, mode), ctx.language)
    if ctx.plan is None:
        return rows

    def checked(b) -> dict:  # verdict(Y·?·N)로 화면이 블록 상태 칩을 그린다
        saved = ctx.block_states.get(b.id)
        if saved is None:
            return {}
        return {"checked": saved.code, "verdict": saved.verdict, **({"stale": True} if saved.verdict == "?" else {})}

    return [row | checked(b) if i < ctx.open_count else row for i, (row, b) in enumerate(zip(rows, ctx.plan.blocks))]


def session_body(ctx, mode: str | None = None) -> dict:
    return {
        "strategy": None if ctx.plan is None else ctx.plan.strategy,
        "blocks": framed_blocks(ctx, mode),
        "open_count": ctx.open_count,
        "chair": messages_body(ctx.chair),
        "guide": messages_body(ctx.guide),
        "followups": [{"quote_id": t.quote_id, "messages": messages_body(t.messages)} for t in ctx.followups],
        "explain": explain_json(ctx.explain),
        "debug": messages_body(ctx.debug),
    }


def body_for(request, result: dict, ctx) -> dict:
    """저장한 뒤 다시 읽은 문맥으로 요청 종류별 본문을 만든다."""
    kind = request.kind
    if kind == "turn":
        chat = ctx.chair if request.mode == "chair" else ctx.guide
        body = {"messages": messages_body(chat), "blocks": blocks_body(ctx.plan, shown_count(ctx, request.mode), ctx.language), "open_count": ctx.open_count}
        if request.event == "block_filled":  # 이름만 달라 통과한 블록 코드의 [내 이름, 튜터 코드의 이름](없으면 빈 목록)
            body["renamed"] = result.get("renamed") or []
            body["withdrawn"] = result.get("withdrawn") or []  # 이번 확인으로 통과를 물린 뒤 블록 id(화면이 그 칸에 '앞 블록이 바뀌었어요'를 보인다)
            body["repeated"] = bool(result.get("repeated"))  # 바뀌지 않은 코드를 다시 확인해 같은 말이 나와 대화에 더하지 않았다(화면이 그 사실을 한 번 알린다)
            body["unsure"] = bool(result.get("unsure"))  # 실행이 뒷받침하지 못했다(실행하지 못하고 코드를 읽어 판정했거나, 확인 전으로 넘어왔거나, 내 블록 탓이라 할 수 없다. 화면이 그 칸을 '확인 전'으로 보인다)
        return body
    if kind == "followup":
        thread = next((t for t in ctx.followups if t.quote_id == request.quote_id), None)
        return {"quote_id": request.quote_id, "messages": messages_body(thread.messages if thread else [])}
    if kind == "fill":
        # 내 이름에 맞춰 채우지 못하면 그 알림(화면이 블록 칸 아래 알림 줄에 보인다)
        return {"block_id": request.block_id, "code": result.get("code", ""), "open_count": ctx.open_count, **({"note": result["note"]} if result.get("note") else {})}
    if kind == "prepare":
        return {"blocks": 0 if ctx.plan is None else len(ctx.plan.blocks), "patterns": list(ctx.patterns)}
    if kind == "debug":
        return {"messages": messages_body(ctx.debug), "step": result.get("move"), "line": result.get("line"), "kind": result.get("kind")}
    if kind == "explain":
        return explain_body(ctx)
    return feedback_body(result)
