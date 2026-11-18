"""ChatGPT 요금제 토큰으로 OpenAI Responses API(https://api.openai.com/v1/responses)를 부른다.
이 경로는 store: false, stream: true만 받는다. response.completed를 받아야 끝난 것으로 본다. 모델 목록도 같은 토큰으로 받는다."""

import json
import sys
import urllib.error
import urllib.request

from app.llm import wire
from app.llm.errors import LlmError, LlmFailed, LlmNotConfigured, LlmTimeout
from app.llm.openai.oauth.token import RELOGIN, access_token, mark
from app.llm.parts import responses_input

URL = "https://api.openai.com/v1/responses"
MODELS_URL = "https://api.openai.com/v1/models"
USAGE_URL = "https://chatgpt.com/settings/usage"
LIMIT = f"ChatGPT 사용 한도에 걸렸어요. ChatGPT 설정의 사용량({USAGE_URL})에서 한도를 확인해 주세요.(429)"  # 끝의 (429)로 화면이 한도 초과로 본다
NOT_ELIGIBLE = "이 ChatGPT 계정(또는 워크스페이스)에서는 앱에 ChatGPT 요금제를 쓸 수 없어요. API 키를 넣어 주세요."
UNAVAILABLE = "ChatGPT 사용량을 지금 확인하지 못했어요. 잠시 뒤에 다시 해 주세요."


def complete(model: str, messages: list[dict], *, images=None, params: dict | None = None) -> dict:
    """max_output_tokens·temperature 같은 값은 이 경로가 받지 않아 보내지 않는다."""
    params = params or {}
    rows = responses_input(messages, images)
    for row in rows:
        if row["role"] == "system":  # system 메시지는 거절된다. 지시문은 developer 메시지로 보낸다
            row["role"] = "developer"
    body = {"model": model, "input": rows, "store": False, "stream": True}
    if params.get("effort"):
        body["reasoning"] = {"effort": params["effort"]}  # 등급표의 추론 정도(low·medium·high)
    if isinstance(params.get("cache_key"), str):
        body["prompt_cache_key"] = params["cache_key"]
    headers = {"Authorization": f"Bearer {access_token()}", "Content-Type": "application/json", "Accept": "text/event-stream"}
    return post_sse(URL, headers, body)


def models() -> list[str]:
    """이 계정에서 고를 수 있는 모델(visibility가 list인 것)의 slug. 서버가 준 차례를 지킨다."""
    payload = wire.post_json(MODELS_URL, {"Authorization": f"Bearer {access_token()}"}, None)
    return [row["slug"] for row in payload.get("models") or []
            if isinstance(row, dict) and row.get("visibility") == "list" and isinstance(row.get("slug"), str)]


def post_sse(url: str, headers: dict, body: dict) -> dict:
    """wire 전송기가 있으면 그것을 쓴다(시험). 전송기는 dict나 SSE 글을 돌려줘도 된다. 다시 보내지 않는다."""
    limit = wire.timeout_seconds()
    if wire._transport is not None:
        reply = wire._transport(url, headers, body, limit)
        return reply if isinstance(reply, dict) else read_sse(reply.splitlines())
    request = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with wire.OPENER.open(request, timeout=limit) as response:
            return read_sse(line.decode("utf-8") for line in response)
    except urllib.error.HTTPError as exc:
        raise refused(exc.code, exc.read(), exc.headers.get("x-request-id") or "") from None
    except TimeoutError as exc:
        raise LlmTimeout("60초를 넘겼습니다.") from exc
    except urllib.error.URLError as exc:
        if "timed out" in str(exc).lower():
            raise LlmTimeout("60초를 넘겼습니다.") from exc
        raise LlmFailed("ChatGPT에 연결하지 못했어요.") from exc


def refused(status: int, raw: bytes, request_id: str = "") -> LlmError:
    """스트림이 열리기 전의 거절. 본문은 {"error": {...}}일 수도 {"detail": "..."}일 수도 있다."""
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        data = {}
    error = data.get("error") if isinstance(data, dict) else None
    return by_code(error if isinstance(error, dict) else {}, status, request_id)


def by_code(error: dict, status: int = 0, request_id: str = "") -> LlmError:
    """오류 코드마다 할 일: 한도 → 사용량 안내, 자격 없음·계정 확인 실패 → 이 연결을 멈추고 알림, 잠깐의 장애 → 나중에 다시."""
    code, param = str(error.get("code") or ""), str(error.get("param") or "")
    print(f"chatgpt responses: status={status} code={code} param={param} request={request_id}"[:300], file=sys.stderr)  # 토큰은 적지 않는다
    if code == "subscription_sharing_usage_limit_exceeded":
        return LlmFailed(LIMIT)
    if code == "subscription_sharing_user_not_eligible":
        mark(NOT_ELIGIBLE)
        return LlmNotConfigured(NOT_ELIGIBLE)
    if code == "subscription_sharing_invalid_user" or (status == 401 and not code):
        mark(RELOGIN)
        return LlmNotConfigured(RELOGIN)
    if code in ("subscription_sharing_usage_unavailable", "subscription_sharing_user_unavailable") or (status == 503 and not code):
        return LlmFailed(UNAVAILABLE)
    return LlmFailed(f"ChatGPT가 요청을 받지 않았어요: 상태 {status or '-'}, {code or '코드 없음'}{f', {param}' if param else ''}")


def read_sse(lines) -> dict:
    """글 조각을 모으고 response.completed의 usage를 붙인다. completed 없이 끝나면 실패다."""
    chunks = []
    for line in lines:
        line = line.strip()
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        event = json.loads(data)
        kind = event.get("type")
        if kind == "response.output_text.delta":
            chunks.append(event.get("delta") or "")
        elif kind == "response.completed":
            return {"output_text": "".join(chunks), "usage": (event.get("response") or {}).get("usage") or {}}
        elif kind == "response.failed":
            raise by_code((event.get("response") or {}).get("error") or {})
        elif kind == "error":
            raise by_code(event.get("error") if isinstance(event.get("error"), dict) else event)
        elif kind == "response.incomplete":
            reason = ((event.get("response") or {}).get("incomplete_details") or {}).get("reason") or ""
            raise LlmFailed(f"ChatGPT의 답이 끝까지 오지 않았어요{f'({reason})' if reason else ''}.")
    raise LlmFailed("ChatGPT의 답이 중간에 끊겼어요.")
