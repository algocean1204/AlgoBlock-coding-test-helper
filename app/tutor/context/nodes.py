"""A2 노드. 저장소는 config["configurable"]["store"]로 받는다(그래프는 DB 위치를 모른다)."""

import sqlite3
from dataclasses import replace

from ..state import MainState, fail
from ..save.respond import explain_body


def store_of(config) -> object:
    return (config or {}).get("configurable", {})["store"]


def load_context(state: MainState, config) -> dict:
    """N1 문항 불러오기."""
    try:
        ctx = store_of(config).load(state["request"].problem_id)
    except sqlite3.Error:
        return fail("store_failed", "저장된 기록을 읽지 못했어요. 앱을 닫았다가 다시 열어 주세요.")
    if ctx is None:
        return fail("not_found", "문제를 찾지 못했어요.")
    shape = (config or {}).get("configurable", {}).get("shape")  # 문항의 방식과 시작 코드는 저장소가 아니라 문제를 가진 쪽(서버)이 안다
    if shape is not None:
        ctx = replace(ctx, **shape(ctx.problem_id, ctx.language))
    return {"ctx": ctx, "open_count": ctx.open_count}


def cached_response(state: MainState, config) -> dict:
    """N2 저장된 결과 확인. 쓸 만하면 튜터 응답을 만들고, 아니면 아무것도 바꾸지 않는다(요청 상태 그대로)."""
    request, ctx = state["request"], state["ctx"]
    if request.kind == "explain" and ctx.explain is not None:
        return {"response": {"status": 200, "body": explain_body(ctx)}}
    if request.kind == "feedback" and ctx.latest_submission is not None:
        try:
            saved = store_of(config).get_feedback(ctx.problem_id)
        except sqlite3.Error:
            return fail("store_failed", "저장된 기록을 읽지 못했어요. 앱을 닫았다가 다시 열어 주세요.")
        if saved is not None and saved.get("submission_id") == ctx.latest_submission.id:
            return {"response": {"status": 200, "body": saved}}
    return {}
