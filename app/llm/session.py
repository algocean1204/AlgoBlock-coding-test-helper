"""llm(모델).use(messages, schema) 가 공급자 폴더로 간다."""

import hashlib
import json
import os
import time

from app.llm import usage
from app.llm.claude.api_key.messages import complete as claude_complete
from app.llm.errors import LlmFailed
from app.llm.openai.api_key.chat import complete as openai_key_complete
from app.llm.openai.oauth.chat import complete as openai_oauth_complete
from app.llm.parse import parse
from app.llm.route import route

_CALLS = {
    ("openai", "api_key"): openai_key_complete,
    ("openai", "oauth"): openai_oauth_complete,
    ("claude", "api_key"): claude_complete,
}


class Handle:
    def __init__(self, model: str):
        self.model = model

    def use(self, messages, schema, *, task=None, images=None, auth=None, **params):
        spec = route(self.model, auth)
        hinted, cache_at, cache_key = _cache_plan(messages)
        if schema is not None:
            names = ", ".join(getattr(schema, "__dataclass_fields__", {}))
            if names:
                hinted = hinted + [{"role": "user", "content": f"JSON만 반환. 키: {names}"}]
        if cache_at is not None:
            params = {**params, "cache_at": cache_at, "cache_key": cache_key}

        def ask(retry=False):
            began = time.monotonic()
            caller = _CALLS.get((spec.provider, spec.auth))
            if caller is None:
                raise LlmFailed("공급자가 연결되지 않았습니다.")
            payload = caller(spec.model, hinted, images=images, params=params)
            usage.record(task, self.model, payload, time.monotonic() - began, retry=retry, effort=params.get("effort"))
            _keep_prompt(task, self.model, hinted, images, params, payload)
            return payload

        payload = ask()
        if schema is None:
            return parse(schema, payload)
        try:
            return parse(schema, payload)
        except LlmFailed:  # 모양이 깨진 답(JSON이 아님, 키 빠짐)은 한 번 다시 받는다. 긴 JSON에서 가끔 따옴표를 풀지 않는다
            return parse(schema, ask(retry=True))


def _keep_prompt(task, model, messages, images, params, payload) -> None:
    """측정 전용: ALGOBLOCK_LLM_PROMPT_DIR이 있을 때만 보낸 프롬프트와 받은 답을 그 폴더에 호출마다 한 파일로 남긴다(대화 한 장면을 다시 돌려 모델 급을 견준다).
    기본은 꺼져 있다. 서버는 자료 폴더 안을 가리키면 끈다. 키는 요청 머리에만 있어 여기에 없다. 이미지는 장수만 적는다."""
    folder = os.environ.get("ALGOBLOCK_LLM_PROMPT_DIR", "").strip()
    if not folder:
        return
    row = {"task": task, "model": model, "params": params, "images": len(images or []), "messages": messages, "reply": payload}
    name = f"{time.strftime('%Y%m%d-%H%M%S')}-{time.monotonic_ns() % 10**9:09d}-{task or 'none'}.json"
    try:
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, name), "w", encoding="utf-8") as file:
            json.dump(row, file, ensure_ascii=False, indent=1)
    except OSError:  # 측정용 사본이다. 못 남겨도 호출은 그대로 쓴다
        pass


def _cache_plan(messages):
    """cache_prefix 표시를 떼어 낸다. (깨끗한 메시지, (메시지 번호, 글자 수), 앞부분 해시)."""
    clean, cache_at, prefix = [], None, []
    for index, message in enumerate(messages):
        at = message.get("cache_prefix")
        clean.append({"role": message.get("role") or "user", "content": message.get("content") or ""})
        if cache_at is None:
            if at:
                cache_at = (index, int(at))
                prefix.append(clean[-1]["content"][: int(at)])
            else:
                prefix.append(clean[-1]["content"])
    if cache_at is None:
        return clean, None, None
    return clean, cache_at, hashlib.sha256("\u0000".join(prefix).encode("utf-8")).hexdigest()[:32]


def llm(model: str) -> Handle:
    return Handle(model)
