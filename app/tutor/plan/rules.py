"""블록 검사와 힌트 다듬기. 모델이 없다."""

import re
from dataclasses import replace

from ..common.scope import KNOWN
from ..common.solution import body_lines, frame_flags
from ..common.talk_rules import hint_problems, repeated_hints
from ..state import BLOCK_KINDS, Block, ErrorInfo


def check_blocks(blocks: list[Block], algorithm: str) -> ErrorInfo | None:
    if not blocks:
        return ErrorInfo("invalid_output", "블록이 없습니다.")
    seen: set[str] = set()
    for block in blocks:
        if block.kind not in BLOCK_KINDS:
            return ErrorInfo("invalid_output", "블록 종류가 아닙니다.")
        if not block.id.strip() or not block.name.strip() or not block.reference.strip():
            return ErrorInfo("invalid_output", "블록 식별자, 이름, 참고 코드가 비었습니다.")
        if block.id in seen:
            return ErrorInfo("invalid_output", "블록 식별자가 겹칩니다.")
        seen.add(block.id)
    if algorithm not in KNOWN:
        return ErrorInfo("invalid_output", "풀이 유형이 아닙니다.")
    return None


def hint_faults(blocks: list[Block], problem: str) -> dict[str, list[str]]:
    """블록 id → 그 블록의 질문이 어긴 원칙들. 어긴 것이 없는 블록은 빠진다."""
    faults = {}
    code = "\n".join(b.reference for b in blocks)
    for index, block in enumerate(blocks):
        later = [b.name for b in blocks[index + 1 :] if b.name.strip()]
        hints = [h.strip() for h in block.hints[:3] if h.strip()]
        found = {item for n, h in enumerate(hints)
                 for item in hint_problems(h, problem=problem, reference=block.reference, later_names=later, clue=(n == 1), code=code)}
        if repeated_hints(hints):
            found.add("같은 질문 되풀이")
        if found:
            faults[block.id] = sorted(found)
    return faults


_LOOP = {"python": re.compile(r"(for|while)\b")}
_LOOP_OTHER = re.compile(r"(for|while)\b|loop\s*\{")


def block_kind(block: Block, language: str) -> str:
    """참고 코드의 첫 구문(틀 줄을 뺀 첫 줄)이 반복이면 loop. 다른 종류는 모델이 붙인 것을 둔다(종류는 블록의 가장 바깥 구조로 정한다)."""
    first = body_lines(block.reference, language)[:1]
    return "loop" if first and _LOOP.get(language, _LOOP_OTHER).match(first[0]) else block.kind


def clean_blocks(blocks: list[Block], problem: str, language: str = "python") -> list[Block]:
    """신호와 질문은 3개까지. 질문 하나라도 원칙을 어기면 그 블록 질문을 비운다(계획은 실패시키지 않는다).

    비운 블록은 대화 때 모델이 질문을 만든다. 느려질 뿐 틀리지 않는다. 반복으로 시작하는 블록의 종류는 loop로 바로잡는다.
    """
    faults = hint_faults(blocks, problem)
    return [replace(block, kind=block_kind(block, language), checks=[c.strip() for c in block.checks[:3] if c.strip()],
                    hints=[] if block.id in faults else [h.strip() for h in block.hints[:3] if h.strip()]) for block in blocks]


# 모델이 낸 줄 구간을 끝내 쓸 수 없을 때의 마지막 길: 가이드 코드를 바깥 수준의 구문 단위로 자른다
_CONT = re.compile(r"\}|else\b|elif\b|except\b|finally\b|catch\b")  # 앞 구문에 이어지는 줄
_OUT = re.compile(r"return\b|print\(|System\.out\.|cout\b|console\.log|fmt\.Print|println!?\(|print!\(")
GENERIC = {  # 이름·목표를 받지 못했을 때 종류에서 만든 일반 문구
    "var_during": ("값 준비", "풀이에 쓸 값을 준비한다"), "loop": ("반복", "무엇을 어떤 순서로 되풀이할지 정한다"),
    "condition": ("조건", "어떤 조건에서 무엇을 할지 정한다"), "branch": ("경우 나누기", "경우마다 무엇을 할지 정한다"),
    "out": ("결과 내기", "구한 결과를 돌려주거나 출력한다"),
}


def _indent(row: str) -> int:
    return len(row) - len(row.lstrip())


def _units(rows: list[str], skip: list[bool], lo: int, hi: int) -> list[list[int]]:
    """[lo, hi) 줄을 바깥 수준(첫 줄의 들여쓰기)의 구문 단위 [처음, 끝]으로 나눈다. 틀 줄·빈 줄·else·닫는 괄호는 앞 단위에 붙는다."""
    base, units = _indent(rows[lo]), []
    for i in range(lo, hi):
        if not units or (not skip[i] and _indent(rows[i]) <= base and not _CONT.match(rows[i].strip())):
            units.append([i, i])
        else:
            units[-1][1] = i
    return units


def _sort(rows: list[str], span: list[int]) -> str:
    first = rows[span[0]].strip()
    if _LOOP_OTHER.match(first):
        return "loop"
    if re.match(r"switch\b|when\b|match\b", first):
        return "branch"
    if re.match(r"if\b", first):
        inner = rows[span[0] + 1 : span[1] + 1]
        top = _indent(rows[span[0]])
        return "branch" if any(_indent(r) == top and re.match(r"\}?\s*(else|elif)\b", r.strip()) for r in inner) else "condition"
    return "out" if _OUT.match(first) else "var_during"


def _groups(rows: list[str], units: list[list[int]]) -> list[list]:
    """[종류, 처음, 끝]. 이어진 변수 준비 줄들과 이어진 결과 줄들은 한 블록, 반복·조건은 하나씩."""
    out = []
    for span in units:
        kind = _sort(rows, span)
        if out and kind == out[-1][0] and kind in ("var_during", "out"):
            out[-1][2] = span[1]
        else:
            out.append([kind, *span])
    return out


def cut_by_rule(code: str, language: str, program: bool = False) -> list[Block]:
    """가이드 코드를 규칙으로 블록으로 자른다. 틀 줄은 앞·뒤 블록에 붙는다. 블록이 5개 미만이면 가장 긴 반복문의 몸통을 한 단계 더 자른다.
    이름·목표는 종류에서 만든 일반 문구다(부르는 쪽이 모델로 바꾼다). 자를 것이 없으면 []."""
    rows = code.splitlines()
    skip = frame_flags(rows, language, program)
    body = [i for i, s in enumerate(skip) if not s]
    if not body:
        return []
    groups = _groups(rows, _units(rows, skip, body[0], body[-1] + 1))
    loops = [g for g in groups if g[0] == "loop" and g[2] > g[1]]
    if len(groups) < 5 and loops:
        longest = max(loops, key=lambda g: g[2] - g[1])
        inner = [i for i in range(longest[1] + 1, longest[2] + 1) if not skip[i]]
        if inner:
            at = groups.index(longest)
            split = _groups(rows, _units(rows, skip, inner[0], longest[2] + 1))
            groups[at:at + 1] = [["loop", longest[1], inner[0] - 1], *split]
    groups[0][1], groups[-1][2] = 0, len(rows) - 1
    blocks = []
    for n, (kind, first, last) in enumerate(groups, 1):
        name, goal = GENERIC[kind]
        blocks.append(Block(id=f"b{n}", kind="var_during" if kind == "out" else kind, name=name, goal=goal,
                            reference="\n".join(rows[first:last + 1]), checks=[goal], lines=[first + 1, last + 1]))
    return blocks
