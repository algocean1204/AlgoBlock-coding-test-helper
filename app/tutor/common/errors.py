"""모델 예외를 오류로 바꾸고, 오류 코드마다 상태 코드를 정한다."""

import re

from ..llm.errors import LlmError, LlmNotConfigured, LlmTimeout
from ..state import ErrorInfo

STATUS = {
    "validation": 400,
    "not_found": 404,
    "block_not_found": 404,
    "block_closed": 409,
    "fill_unavailable": 409,
    "already_started": 409,
    "not_submitted": 409,
    "ingest_failed": 422,
    "store_failed": 500,
    "invalid_output": 502,
    "llm_auth_failed": 401,
    "llm_rate_limited": 429,
    "llm_failed": 502,
    "llm_not_configured": 503,
    "llm_timeout": 504,
}


def llm_error(exc: LlmError) -> ErrorInfo:
    if isinstance(exc, LlmTimeout):
        return ErrorInfo("llm_timeout", "60초를 넘겼어요.")
    # 공급자 상태 코드는 app/llm(wire.post_json)가 글 끝 괄호에 싣는다: 401·403 → LlmNotConfigured, 429(다시 보내도 안 됨) → LlmFailed
    status = re.search(r"\((\d{3})\)", str(exc))
    if status and status.group(1) in ("401", "403"):
        return ErrorInfo("llm_auth_failed", "모델 키가 맞지 않아요. '설정'의 'AI 연결'에서 키를 다시 넣어 주세요.")
    if status and status.group(1) == "429":
        said = str(exc).replace(status.group(0), "").strip()  # 공급자 경로가 사람 말을 실었으면(ChatGPT 사용 한도 안내) 그 말을 쓴다
        return ErrorInfo("llm_rate_limited", said if said and not said.startswith("공급자 오류") else "모델 사용 한도에 걸렸어요. 잠시 뒤에 다시 해 주세요.")
    if isinstance(exc, LlmNotConfigured):
        return ErrorInfo("llm_not_configured", "AI가 연결되어 있지 않아요. ‘설정’의 ‘AI 연결’에서 연결해 주세요.")
    return ErrorInfo("llm_failed", str(exc).strip() or "AI 서비스 오류")


def stop_on_error(name: str):
    """조건 엣지. 오류가 있으면 end, 없으면 name."""

    def route(state) -> str:
        return "end" if state.get("error") else name

    return route
