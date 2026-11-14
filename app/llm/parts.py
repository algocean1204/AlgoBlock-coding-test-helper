"""메시지에 이미지를 붙인다. 공급자 폴더는 서로를 부르지 않는다."""

import base64
import os


def _b64(image) -> str:
    if isinstance(image, str):
        return image
    return base64.b64encode(image).decode("ascii")


def responses_input(messages: list[dict], images=None) -> list[dict]:
    rows = []
    for message in messages:
        rows.append(
            {
                "role": message.get("role") or "user",
                "content": [{"type": "input_text", "text": message.get("content") or ""}],
            }
        )
    if images and rows:
        for image in images:
            rows[-1]["content"].append(
                {"type": "input_image", "image_url": f"data:image/png;base64,{_b64(image)}"}
            )
    return rows


def cache_split(text: str, at: int | None) -> list[dict] | None:
    """캐시 경계에서 글을 두 블록으로 나눈다. 앞 블록에 cache_control을 붙인다(Anthropic 모양)."""
    if not at or at >= len(text):
        return None
    mark = {"type": "ephemeral"}
    ttl = os.environ.get("ALGOBLOCK_LLM_CACHE_TTL", "").strip()
    if ttl == "1h":
        mark["ttl"] = "1h"
    return [{"type": "text", "text": text[:at], "cache_control": mark}, {"type": "text", "text": text[at:]}]
