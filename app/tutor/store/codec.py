"""계획과 해설을 JSON 글로. 옛 계획(필드가 적은 것)도 읽힌다."""

import json
from dataclasses import asdict, fields

from ..state import Block, BlockPlan, Explain, Section

_BLOCK_FIELDS = {item.name for item in fields(Block)}


def plan_to_json(plan: BlockPlan | None) -> str | None:
    if plan is None:
        return None
    return json.dumps(asdict(plan), ensure_ascii=False)


def plan_from_json(raw: str | None) -> BlockPlan | None:
    if not raw:
        return None
    data = json.loads(raw)
    blocks = [Block(**{k: v for k, v in item.items() if k in _BLOCK_FIELDS}) for item in data["blocks"]]
    return BlockPlan(
        strategy=data["strategy"],
        score=data["score"],
        blocks=blocks,
        algorithm=data.get("algorithm", ""),
        out_of_scope=data.get("out_of_scope", False),
        link=data.get("link", ""),
        settled=data.get("settled", False),
    )


def explain_to_json(explain: Explain | None) -> str | None:
    if explain is None:
        return None
    return json.dumps(asdict(explain), ensure_ascii=False)


def explain_from_json(raw: str | None) -> Explain | None:
    if not raw:
        return None
    data = json.loads(raw)
    sections = [Section(**item) for item in data["sections"]]
    return Explain(sections=sections)


