"""응답 글에서 JSON을 골라 스키마로 만든다."""

import json
from dataclasses import MISSING, fields, is_dataclass
from typing import Any, get_args, get_origin, get_type_hints

from app.llm.errors import LlmFailed


def text_of(payload: dict) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    output = payload.get("output")
    if isinstance(output, list):
        chunks = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and isinstance(part.get("text"), str):
                        chunks.append(part["text"])
            elif isinstance(item.get("text"), str):
                chunks.append(item["text"])
        if chunks:
            return "\n".join(chunks)
    content = payload.get("content")
    if isinstance(content, list):
        texts = [part.get("text", "") for part in content if isinstance(part, dict)]
        if any(texts):
            return "".join(texts)
    if isinstance(content, str):
        return content
    raise LlmFailed("모양 불일치")


def json_of(text: str) -> Any:
    raw = text.strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:  # 글 안의 따옴표를 풀지 않은 JSON 등. 밖으로 새면 서버 오류가 된다
                pass
        raise LlmFailed("모양 불일치") from None


def coerce(schema: type, data: Any) -> Any:
    if is_dataclass(schema) and isinstance(data, schema):
        return data
    if not is_dataclass(schema) or not isinstance(data, dict):
        raise LlmFailed("모양 불일치")
    hints = get_type_hints(schema)
    kwargs = {}
    for item in fields(schema):
        if item.name not in data:
            # 기본값이 있는 필드는 빠져도 된다.
            if item.default is MISSING and item.default_factory is MISSING:
                raise LlmFailed("모양 불일치")
            continue
        kwargs[item.name] = _value(hints[item.name], data[item.name])
    return schema(**kwargs)


def _value(typ: Any, value: Any) -> Any:
    origin = get_origin(typ)
    if origin is None and is_dataclass(typ):
        return coerce(typ, value)
    if origin is list:
        (inner,) = get_args(typ)
        if not isinstance(value, list):
            raise LlmFailed("모양 불일치")
        return [_value(inner, item) for item in value]
    if typ is str:
        if not isinstance(value, str):
            raise LlmFailed("모양 불일치")
        return value
    if typ is bool:
        if not isinstance(value, bool):
            raise LlmFailed("모양 불일치")
        return value
    if typ is int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise LlmFailed("모양 불일치")
        return value
    raise LlmFailed("모양 불일치")


def parse(schema: type | None, payload: dict) -> Any:
    """schema가 None이면 글 모드다. 글을 그대로 돌려준다."""
    if schema is None:
        return text_of(payload)
    return coerce(schema, json_of(text_of(payload)))
