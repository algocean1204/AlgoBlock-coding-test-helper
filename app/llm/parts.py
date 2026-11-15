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


def cache_split(text: str, at: int | None, more=()) -> list[dict] | None:
    """캐시 경계(글자 수 at, 뒤쪽 경계 more)에서 글을 나눈다. 경계 앞 블록마다 cache_control을 붙인다(Anthropic 모양)."""
    cuts = sorted({n for n in (at, *more) if n and n < len(text)})
    if not cuts:
        return None
    mark = {"type": "ephemeral"}
    ttl = os.environ.get("ALGOBLOCK_LLM_CACHE_TTL", "").strip()
    if ttl == "1h":
        mark["ttl"] = "1h"
    edges = [0, *cuts, len(text)]
    blocks = [{"type": "text", "text": text[a:b]} for a, b in zip(edges, edges[1:])]
    for block in blocks[:-1]:
        block["cache_control"] = dict(mark)
    return blocks
