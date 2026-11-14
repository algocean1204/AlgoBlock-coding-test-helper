"""OpenAI Responses API. 키는 Bearer다."""

import os

from app.llm.errors import LlmNotConfigured
from app.llm.parts import responses_input
from app.llm.wire import post_json

URL = "https://api.openai.com/v1/responses"
MODELS_URL = "https://api.openai.com/v1/models"  # 모델 목록(돈이 들지 않는다)


def _key() -> str:
    key = os.environ.get("OPENAI_API_KEY", "").strip() or os.environ.get("ALGOBLOCK_LLM_API_KEY", "").strip()
    if not key:
        raise LlmNotConfigured("모델이나 키가 없습니다.")
    return key


def complete(model: str, messages: list[dict], *, images=None, params: dict | None = None) -> dict:
    params = params or {}
    body = {"model": model, "input": responses_input(messages, images), "store": False}
    if "temperature" in params:
        body["temperature"] = params["temperature"]
    if params.get("effort"):
        body["reasoning"] = {"effort": params["effort"]}
    if params.get("cache_key"):
        body["prompt_cache_key"] = params["cache_key"]  # 같은 앞부분을 같은 서버로 보내 자동 캐시 적중을 높인다
    return post_json(
        URL,
        {"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
        body,
    )


def models() -> list[str]:
    """이 키로 쓸 수 있는 모델 이름들."""
    payload = post_json(MODELS_URL, {"Authorization": f"Bearer {_key()}"}, None)
    return [row["id"] for row in payload.get("data") or [] if isinstance(row, dict) and isinstance(row.get("id"), str)]
