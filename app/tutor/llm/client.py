"""llm(모델).use(...) 한 번이 모델 노드 하나다. 제한 시간은 60초.

schema가 None이면 글 모드다. JSON을 요구하지 않고 모델 글을 그대로 돌려준다.

use_llm(가짜) 안에서는 가짜가, 밖에서는 공급자 연결 코드(app.llm)가 받는다.
app.llm이 이미 import되는 곳(서버 안)이면 그것을 바로 쓰고,
아니면 저장소 루트(app/의 위)를 경로에 더해 app/llm을 app.llm으로 부른다.
"""

import os
import types
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import MISSING, fields, is_dataclass
from typing import Any, Union, get_args, get_origin, get_type_hints

from .errors import LlmFailed, LlmNotConfigured, LlmTimeout
from .themes import pick

_current: ContextVar[Any] = ContextVar("algoblock_llm", default=None)


def timeout_seconds() -> float:
    raw = os.environ.get("ALGOBLOCK_LLM_TIMEOUT", "60")
    try:
        return float(raw)
    except ValueError:
        return 60.0


def coerce(schema: type, data: Any) -> Any:
    if is_dataclass(schema) and isinstance(data, schema):
        return data
    if not is_dataclass(schema) or not isinstance(data, dict):
        raise LlmFailed("모양이 맞지 않습니다.")
    hints = get_type_hints(schema)
    kwargs = {}
    for item in fields(schema):
        if item.name not in data:
            # 기본값이 있는 필드는 모델이 빠뜨려도 된다(예: 블록의 checks, hints).
            if item.default is MISSING and item.default_factory is MISSING:
                raise LlmFailed("모양이 맞지 않습니다.")
            continue
        kwargs[item.name] = _coerce_value(hints[item.name], data[item.name])
    return schema(**kwargs)


def _coerce_value(typ: Any, value: Any) -> Any:
    origin = get_origin(typ)
    if origin is None and is_dataclass(typ):
        return coerce(typ, value)
    if origin in (list,):
        (inner,) = get_args(typ)
        if not isinstance(value, list):
            raise LlmFailed("모양이 맞지 않습니다.")
        return [_coerce_value(inner, item) for item in value]
    if origin is Union or origin is types.UnionType:
        return _coerce_union(typ, value)
    if typ is str:
        if not isinstance(value, str):
            raise LlmFailed("모양이 맞지 않습니다.")
        return value
    if typ is bool:
        if not isinstance(value, bool):
            raise LlmFailed("모양이 맞지 않습니다.")
        return value
    if typ is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise LlmFailed("모양이 맞지 않습니다.")
        return value
    raise LlmFailed("모양이 맞지 않습니다.")


def _coerce_union(typ: Any, value: Any) -> Any:
    if value is None:
        if type(None) not in get_args(typ):
            raise LlmFailed("모양이 맞지 않습니다.")
        return None
    for arg in get_args(typ):
        if arg is type(None):
            continue
        try:
            return _coerce_value(arg, value)
        except LlmFailed:
            continue
    raise LlmFailed("모양이 맞지 않습니다.")


class FakeLlm:
    """task마다 준비한 응답을 차례로 준다. calls에 입력 기록이 남는다."""

    def __init__(self, scripts: dict[str, list] | None = None, delay: float = 0):
        self.scripts = {key: list(value) for key, value in (scripts or {}).items()}
        self.delay = delay
        self.calls: list[dict] = []

    def run(self, task: str, messages: list[dict], schema: type | None, images: list | None = None, params=None):
        self.calls.append(
            {"task": task, "messages": messages, "schema": schema, "images": images, "params": params or {}}
        )
        if self.delay > timeout_seconds():
            raise LlmTimeout("60초를 넘겼습니다.")
        queue = self.scripts.get(task)
        if not queue:
            raise LlmFailed(f"가짜 응답 없음: {task}")
        item = queue.pop(0)
        if isinstance(item, LlmFailed | LlmTimeout | LlmNotConfigured):
            raise item
        if schema is None:
            if not isinstance(item, str):
                raise LlmFailed("모양이 맞지 않습니다.")
            return item
        return coerce(schema, item)


def cached_user(lines: list[str], head: int) -> dict:
    """사용자 메시지 하나. 앞 head줄(시스템 다음의 고정 앞부분: 문제 글 등)이 캐시 대상이다.

    cache_prefix는 그 앞부분의 글자 수다. 공급자가 캐시 표시(Claude cache_control)를 그 경계에 붙이고,
    표시가 없는 공급자는 앞부분이 같다는 것만으로 자동 캐시를 탄다. 바뀌는 내용은 뒤 줄에 둔다.
    """
    content = "\n".join(lines)
    return {"role": "user", "content": content, "cache_prefix": len("\n".join(lines[:head]))}


DEFAULT_MODEL = "claude/claude-haiku-5-5"


def model_name() -> str:
    """기본 모델 이름(기록용). 실제 호출 모델은 task의 테마로 정해진다."""
    return os.environ.get("ALGOBLOCK_LLM_MODEL", "").strip() or DEFAULT_MODEL


class _Using:
    def __init__(self, model: str, fake: FakeLlm | None):
        self.model = model
        self.fake = fake

    def use(self, messages, schema, *, task=None, images=None, **params):
        model, effort = pick(task)  # 테마표가 모델과 추론 정도를 고른다(llm/themes.py)
        if self.model and self.model != model_name():
            model = self.model  # 부르는 쪽이 모델을 직접 정했으면 그대로
        params.setdefault("effort", effort)
        if self.fake is not None:
            return self.fake.run(task or model, messages, schema, images, {**params, "model": model})
        return _backend_use(model, messages, schema, task=task, images=images, **params)


def _backend_session():
    """app.llm.session을 찾는다. 서버 안에서는 바로 import된다."""
    import importlib
    import sys
    from pathlib import Path

    try:
        return importlib.import_module("app.llm.session")
    except ModuleNotFoundError as exc:
        if exc.name not in ("app", "app.llm", "app.llm.session"):
            raise
    root = Path(__file__).resolve().parents[3]  # 저장소 루트(app/tutor/llm/client.py에서 세 단계 위)
    if (root / "app" / "llm" / "session.py").is_file():
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        return importlib.import_module("app.llm.session")
    raise LlmNotConfigured("app/llm(모델 연결 코드)을 찾지 못했습니다.")


def record_usage(task, model: str, raw_usage: dict, seconds: float, effort=None) -> None:
    """app.llm을 거치지 않는 연결(개발용 Claude Code)의 호출도 같은 사용 기록에 남긴다. raw_usage는 Anthropic 모양의 usage."""
    try:
        _backend_session().usage.record(task, model, {"usage": raw_usage}, seconds, effort=effort)
    except LlmNotConfigured:  # 기록은 덤이다
        pass


def _backend_use(model, messages, schema, *, task=None, images=None, **params):
    session = _backend_session()
    try:
        return session.llm(model).use(messages, schema, task=task, images=images, **params)
    except Exception as exc:
        name = type(exc).__name__
        if name == "LlmNotConfigured":
            raise LlmNotConfigured(str(exc)) from None
        if name == "LlmTimeout":
            raise LlmTimeout(str(exc)) from None
        if name == "LlmFailed":
            # backend 문구 "모양 불일치"를 문서 문구로 맞춘다.
            message = str(exc).replace("모양 불일치", "모양이 맞지 않습니다.")
            raise LlmFailed(message or "공급자 오류") from None
        raise


def llm(model: str | None = None):
    return _Using(model, _current.get())


@contextmanager
def use_llm(client):
    token = _current.set(client)
    try:
        yield client
    finally:
        _current.reset(token)
