"""Anthropic Messages API. 키는 x-api-key 다.

구독(Free·Pro·Max) OAuth는 두지 않는다. Anthropic 정책이 제3자 앱의 claude.ai 로그인과 구독 자격증명 경유를 금지한다
(code.claude.com/docs/en/legal-and-compliance). temperature 등 샘플링 값은 보내지 않는다(최신 모델은 400).
"""

import base64
import os

from app.llm.errors import LlmFailed, LlmNotConfigured
from app.llm.parts import cache_split
from app.llm.wire import post_json

URL = "https://api.anthropic.com/v1/messages"
MODELS_URL = "https://api.anthropic.com/v1/models?limit=1000"  # 모델 목록(돈이 들지 않는다). 1000개면 한 쪽에 다 온다
SHORT = 1024  # 이보다 짧은 답(판정 [check] 한 줄 등)
THINK_ROOM = 2048  # 생각이 기본으로 켜진 모델은 생각 토큰도 max_tokens에 든다. 짧은 답에는 그 몫을 더한다


def _key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip() or os.environ.get("ALGOBLOCK_LLM_API_KEY", "").strip()
    if not key:
        raise LlmNotConfigured("모델이나 키가 없습니다.")
    return key


def complete(model: str, messages: list[dict], *, images=None, params: dict | None = None) -> dict:
    """effort(low·medium·high)는 output_config로 보낸다. temperature 등 샘플링 값은 보내지 않는다."""
    params = params or {}
    system, rows = _split(messages, images, params.get("cache_at"))
    want = int(params.get("max_tokens") or 16000)
    body = {"model": model, "max_tokens": want + THINK_ROOM if want < SHORT else want, "messages": rows}
    if params.get("effort"):
        body["output_config"] = {"effort": params["effort"]}
    if system:
        body["system"] = system
    payload = post_json(
        URL,
        {
            "x-api-key": _key(),
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        body,
    )
    if payload.get("stop_reason") in ("refusal", "max_tokens") and want >= SHORT:
        raise LlmFailed("모델이 답을 끝내지 못했습니다.")  # 잘린 JSON을 모양 오류로 넘기지 않는다
    return payload


def models() -> list[str]:
    """이 키로 쓸 수 있는 모델 이름들."""
    payload = post_json(MODELS_URL, {"x-api-key": _key(), "anthropic-version": "2023-06-01"}, None)
    return [row["id"] for row in payload.get("data") or [] if isinstance(row, dict) and isinstance(row.get("id"), str)]


def _split(messages: list[dict], images, cache_at=None) -> tuple[str, list[dict]]:
    """system은 본문 밖으로. cache_at=(메시지 번호, 글자 수)면 그 메시지를 캐시 경계에서 두 블록으로 나눈다."""
    system = []
    rows = []
    for index, message in enumerate(messages):
        role = message.get("role") or "user"
        text = message.get("content") or ""
        if role == "system":
            system.append(text)
            continue
        if role not in {"user", "assistant"}:
            role = "user"
        blocks = cache_split(text, cache_at[1], cache_at[2]) if cache_at and cache_at[0] == index else None
        rows.append({"role": role, "content": blocks or text})
    if not rows:
        rows = [{"role": "user", "content": ""}]
    if images:
        last = rows[-1]["content"]
        rows[-1]["content"] = [
            *(last if isinstance(last, list) else [{"type": "text", "text": last}]),
            *[
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image if isinstance(image, str) else base64.b64encode(image).decode("ascii"),
                    },
                }
                for image in images
            ],
        ]
    return "\n".join(system), rows
