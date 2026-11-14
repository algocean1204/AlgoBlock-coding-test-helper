"""풀이 가이드를 프롬프트에 넣는 한 덩이. 문제마다 바뀌지 않으므로 캐시되는 앞부분(문제 글 바로 뒤)에 둔다.
블록 reference(가이드 코드의 줄 구간)의 틀 줄 판정도 여기 둔다(블록 코드 확인·세션 본문·계획 다듬기가 같이 쓴다)."""

import builtins
import keyword
import re


def solution_of(state):
    """이번 요청에서 만든 가이드가 있으면 그것, 아니면 저장된 것."""
    return state.get("solution") or state["ctx"].solution


def guide_checked(state) -> bool:
    """풀이 가이드가 있고 공개 예시를 통과했다. 아니면 그 코드로 이은 프로그램의 실행은 어느 블록의 판정도 될 수 없다."""
    guide = solution_of(state)
    return guide is not None and guide.verified


def solution_lines(state, code: bool = False) -> list[str]:
    """[] 또는 [한 덩이]. code=True면 정답 코드까지 넣는다(해설, 진단, 피드백처럼 풀이 전체를 봐야 하는 일)."""
    guide = solution_of(state)
    if guide is None:
        return []
    parts = ["풀이 가이드(사용자에게 보이지 않는다. 모든 말은 이 풀이 하나를 바탕으로 한다): " + guide.approach]
    if guide.clues:
        parts.append("단서: " + " / ".join(guide.clues))
    if guide.steps:
        parts.append("단계: " + " / ".join(guide.steps))
    if code:
        parts.append(f"정답 코드(그대로 보여 주지 않는다):\n{guide.code}")
    return ["\n".join(parts)]


# 틀 줄: 블록 reference에 들어 있지만 답이 아닌 줄(import, 진입 함수·클래스 머리, 닫는 괄호, 표준 입력 읽기 준비). 사용자는 블록 칸에 적지 않는다.
# 함수 머리는 진입 함수(solution, 그것을 감싸는 class Solution, 표준 입출력 문제의 main과 class Main)만 본다. 도우미 함수의 머리는 풀이의 일부다
_FRAME_PY = re.compile(r"def (?:solution|main)\b.*:|class Solution\b.*:|import \S.*|from \S+ import .+|\w+ = sys\.stdin(?:\.buffer)?\.read(?:line)?"
                       r"|if __name__ == .+:|main\(\)")
_FRAME = re.compile(
    r"import\b.*|#include\b.*|using\s.+;|use\s.+;|package\s.+|\"[\w./-]+\"|\)"  # 머리말(go의 여러 줄 import 포함)
    r"|(public\s+)?class (?:Solution|Main)\b.*\{|[\w<>\[\],\s]*\b(?:solution|main)\s*\([^;]*\)[^;=]*\{|\}\s*;?"
    r"|(?:const|let|var) .+ = require\([\"']fs[\"']\)(?:\.readFileSync\(.*)?;?"  # js의 표준 입력 전체 읽기
)


def _plain(line: str, language: str) -> str:
    """주석을 떼고 연속 공백을 하나로. 줄 끝 주석도 뗀다(가이드 코드에는 줄 끝 주석이 있고 사용자는 적지 않는다)."""
    mark = "#" if language == "python" else "//"
    return re.sub(r"\s+", " ", re.sub(rf"(^|\s){re.escape(mark)}.*", "", line)).strip()


def frame_line(line: str, language: str) -> bool:
    plain = _plain(line, language)
    return bool(plain) and bool((_FRAME_PY if language == "python" else _FRAME).fullmatch(plain))


_NOT_BRACE = re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])'|/\*.*?\*/|//.*")  # 괄호를 세지 않는 곳: 문자열, 글자 하나, 주석


def _braces_as_body(rows: list[str], skip: list[bool]) -> None:
    """닫는 괄호 줄 '}'은 뼈대(틀 줄이 연 진입 클래스·함수)를 닫을 때만 틀 줄이다. 이 코드 안의 알맹이가 연 괄호를 닫거나,
    알맹이보다 앞에 오는 '}'(앞 블록에서 연 것)은 알맹이다. 반복문을 닫는 '}'가 tail로 실려 중괄호 없는 for 뒤에 덧붙었다."""
    opened, body_seen = [], False
    for i, row in enumerate(rows):
        plain = _NOT_BRACE.sub("", row)
        if skip[i] and re.fullmatch(r"\s*\}\s*;?\s*", plain):
            if opened:
                skip[i] = opened.pop() == "frame"
            elif not body_seen:
                skip[i] = False
            continue
        for ch in plain:
            if ch == "{":
                opened.append("frame" if skip[i] else "body")
            elif ch == "}" and opened:
                opened.pop()
        body_seen = body_seen or (not skip[i] and bool(row.strip()))


def frame_flags(rows: list[str], language: str, program: bool) -> list[bool]:
    """줄마다 틀 줄이거나 빈 줄인가. 프로그램 방식 c++의 맨 끝 'return 0;'(main을 닫는 줄)도 틀 줄이다(함수 방식에서는 답일 수 있다)."""
    skip = [frame_line(row, language) or not row.strip() for row in rows]
    if language != "python":
        _braces_as_body(rows, skip)
    if program and language == "cpp":
        for i in range(len(rows) - 1, -1, -1):
            if not skip[i]:
                skip[i] = _plain(rows[i], language) == "return 0;"
                if not skip[i]:
                    break
    # 머리말은 맨 앞에서 마지막 틀 줄까지다(그 사이 주석 포함). 꼬리는 맨 뒤 첫 틀 줄부터(그 뒤 주석 포함).
    # 주석 뒤의 진입 함수 줄('def solution(…)', 'func solution(…) {')을 알맹이로 봐 사용자가 블록 1을 적으면 그 줄이 사라졌다
    note = [bool(row.strip()) and not _plain(row, language) for row in rows]
    lead = 0
    while lead < len(rows) and (skip[lead] or note[lead]):
        lead += 1
    last = max((i for i in range(lead) if skip[i] and rows[i].strip()), default=-1)
    end = len(rows)
    while end > 0 and (skip[end - 1] or note[end - 1]):
        end -= 1
    first = min((i for i in range(end, len(rows)) if skip[i] and rows[i].strip()), default=len(rows))
    for i in [*range(last), *range(first, len(rows))]:
        skip[i] = skip[i] or note[i]
    return skip


def open_braces(code: str, language: str, program: bool = False) -> int:
    """연 중괄호 수 − 닫은 중괄호 수(문자열·주석 밖, 틀 줄은 세지 않는다)."""
    rows = (code or "").splitlines()
    return sum(_NOT_BRACE.sub("", row).count("{") - _NOT_BRACE.sub("", row).count("}") for row, skip in zip(rows, frame_flags(rows, language, program)) if not skip)


def body_lines(code: str, language: str, program: bool = False) -> list[str]:
    """틀 줄·빈 줄·주석을 뺀 줄(정규화한 꼴)."""
    rows = (code or "").splitlines()
    return [_plain(row, language) for row, skip in zip(rows, frame_flags(rows, language, program)) if not skip and _plain(row, language)]


_TOKEN = re.compile(r"\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|[A-Za-z_]\w*|\d+(?:\.\d+)?|//=|\*\*=|<<=|>>=|[-+*/%&|^:<>!=]=|\S")
_ASSIGN = {"=", "+=", "-=", "*=", "/=", "//=", "%=", "**=", "&=", "|=", "^=", "<<=", ">>=", ":="}


def _bound(rows: list[list[str]]) -> set[str]:
    """대입의 왼쪽(반복 변수, 'a, b =' 포함)에 나온 이름. 점 뒤의 이름과 괄호 안의 이름(키워드 인자)은 빼낸다."""
    names = set()
    for toks in rows:
        loop, depth = toks[:1] == ["for"], 0
        for i, tok in enumerate(toks):
            depth += (tok in "([{") - (tok in ")]}")
            if not re.fullmatch(r"[A-Za-z_]\w*", tok) or toks[i - 1:i] in (["."], ["::"]) or depth > loop:
                continue
            j = i
            while toks[j + 1:j + 2] == [","] and j + 2 < len(toks) and re.fullmatch(r"[A-Za-z_]\w*", toks[j + 2]):
                j += 2  # 'a, b = …', 'for i, c in …'
            after = toks[j + 1] if j + 1 < len(toks) else ""
            # 'for (auto x : xs)'의 x는 반복 변수지만, Python 'for x in xs:'의 xs(줄 끝 ':' 앞)는 도는 대상이다
            if after in _ASSIGN or (loop and (after == "in" or after == ":" and "in" not in toks[:i])):
                names.update(toks[i:j + 1:2])
    return names


def _renamed(lines: list[str], allowed: set[str] | None = None) -> list[list[str]]:
    """줄마다 낱말로 쪼개고, 이름을 바꿔도 되는 이름(allowed. 없으면 그 코드에서 대입한 이름)을 처음 나온 순서의 번호로 바꾼다(점 뒤 이름은 그대로)."""
    rows = [_TOKEN.findall(line) for line in lines]
    names = _first_seen(rows) if allowed is None else [n for n in dict.fromkeys(t for toks in rows for t in toks) if n in allowed]
    order = {name: n for n, name in enumerate(names)}
    return [[f"#{order[tok]}" if tok in order and toks[i - 1:i] not in (["."], ["::"]) else tok
             for i, tok in enumerate(toks)] for toks in rows]


def _first_seen(rows: list[list[str]]) -> list[str]:
    """대입한 이름을 처음 나온 순서로(점 뒤 이름은 빼낸다)."""
    bound, seen = _bound(rows), {}
    for toks in rows:
        for i, tok in enumerate(toks):
            if tok in bound and toks[i - 1:i] not in (["."], ["::"]):
                seen.setdefault(tok, None)
    return list(seen)


def bound_names(lines: list[str]) -> set[str]:
    """정규화한 줄들(body_lines)에서 대입한 이름."""
    return _bound([_TOKEN.findall(line) for line in lines])


def _shape(code: str, language: str, program: bool) -> list[int]:
    """알맹이 줄의 앞 공백을 서로 다른 값의 순위로(2칸·4칸 들여쓰기는 같은 모양)."""
    rows = (code or "").splitlines()
    leads = [_lead(row) for row, skip in zip(rows, frame_flags(rows, language, program)) if not skip and _plain(row, language)]
    order = sorted(set(leads))
    return [order.index(lead) for lead in leads]


def same_code(code: str, reference: str, language: str, program: bool = False) -> bool:
    """공백·빈 줄·주석·틀 줄, 또는 새로 만드는 이름(created_names. +=·-=로 고쳐 쓰는 이름은 아니다)만 다르면 참. Python은 들여쓰기 모양도 같아야 한다.
    피드백이 '이름만 다른 같은 코드'를 셀 때 쓴다. 블록 코드 확인의 통과에는 쓰지 않는다(틀 줄·문자열 안의 차이를 같다고 본다)."""
    body = body_lines(reference, language, program)
    mine = body_lines(code, language, program)
    if language == "python" and _shape(code, language, program) != _shape(reference, language, program):
        return False
    plan_fresh, mine_fresh = {n for n, *_ in created_names(reference, language, program)}, {n for n, *_ in created_names(code, language, program)}
    return bool(body) and (mine == body or _renamed(mine, mine_fresh) == _renamed(body, plan_fresh))


_NAME = re.compile(r"[A-Za-z_]\w*")
# 후보에서 빼는 낱말: 파이썬은 예약어·내장 이름, 중괄호 언어는 예약어·기본 타입(Java의 'sum' 같은 변수는 후보다)
_WORDS = {"python": set(keyword.kwlist) | set(dir(builtins)), "other": set(
    "int long double float char boolean bool byte short void var let const auto new return if else for while do break continue class "
    "public private static final true false null nullptr this struct using namespace std func fn mut val fun string range in of self "
    "unsigned size_t vector cin cout endl fmt".split())}


def name_candidates(code: str, reference: str, language: str, missing: str, plan_words: set[str], program: bool = False) -> list[str]:
    """실행에서 없는 이름(missing, 계획 코드의 이름)을 대신할 사용자 이름 후보(해 볼 차례대로).
    계획의 이 블록이 missing을 대입한 자리와 같은 자리에서 사용자가 대입한 이름 → 계획에 없는 이름 → 이 블록에서 값을 바꾸는 이름(대입, 메서드 호출 앞).
    예약어·내장 이름, 점 뒤 이름, 함수 이름, 타입 자리 이름은 뺀다."""
    rows = [_TOKEN.findall(line) for line in body_lines(code, language, program)]
    names, changed = [], _bound(rows)
    for toks in rows:
        for i, tok in enumerate(toks):
            after = toks[i + 1] if i + 1 < len(toks) else ""
            typed = language != "python" and (bool(_NAME.fullmatch(after)) or (tok[0].isupper() and after in (".", "[", "<")))
            if not _NAME.fullmatch(tok) or tok in _WORDS["python" if language == "python" else "other"] or toks[i - 1:i] in (["."], ["::"]) or after == "(" or typed:
                continue
            names.append(tok)
            if after == "." and toks[i + 3:i + 4] == ["("]:
                changed.add(tok)  # 'items.sort()'처럼 값을 바꾸는 메서드 호출
    names = [name for name in dict.fromkeys(names) if name != missing]
    plan_bound, my_bound = first_bound(reference, language, program), _first_seen(rows)
    same = plan_bound.index(missing) if missing in plan_bound else len(my_bound)
    # 자리 후보도 계획에 있는 이름(양쪽이 같이 쓰는 이름)은 뺀다: 함수 인자가 다른 변수의 첫 후보가 되었다
    first = [my_bound[same]] if same < len(my_bound) and my_bound[same] in names and my_bound[same] not in plan_words else []
    return list(dict.fromkeys(first + [n for n in names if n not in plan_words] + [n for n in names if n in changed]))


def first_bound(code: str, language: str, program: bool = False) -> list[str]:
    """코드에서 대입한 이름을 처음 나온 순서로(틀 줄은 뺀다)."""
    return _first_seen([_TOKEN.findall(line) for line in body_lines(code, language, program)])


# 이름 앞에 오면 선언이 아닌 낱말(return x; / else x; / new X …)과 타입을 적지 않는 선언 낱말
_NOT_TYPE = set("return new throw else case delete goto typedef sizeof instanceof throws import package using namespace class struct interface "
                "enum extends implements break continue yield await in of is as do".split())
_LOOSE = {"auto", "var", "val", "let", "const", "mut", "lateinit"}
_TYPE_TOKEN = re.compile(r"[A-Za-z_]\w*|[<>\[\]*&?.,]|::")


def _type_text(toks: list[str]) -> str:
    """선언에 적힌 타입을 공백 없이(const·final·static·&는 뺀다). auto·var·val·let은 빈 글."""
    kept = [t for t in toks if t not in ("const", "final", "static", "mut", "&", "&&", "lateinit")]
    text = "".join(kept)
    return "" if not text or text in _LOOSE else text


def _params(inside: list[str], language: str) -> list[tuple[str, str, str]]:
    """정의 줄 괄호 안 낱말에서 매개변수 (이름, 'param', 타입)."""
    out, seg, depth = [], [], 0
    for tok in [*inside, ","]:
        depth += (tok in "(<[{") - (tok in ")>]}")
        if tok == "," and depth == 0:
            seg = seg[:seg.index("=")] if "=" in seg else seg
            names = [t for t in seg if _NAME.fullmatch(t) and t != "self"]
            if language == "python" and names:
                out.append((names[0], "param", ""))
            elif language == "go" and names:  # Go 'a, b int', 'parent []int': 이름이 앞
                out.append((names[0], "param", _type_text(seg[seg.index(names[0]) + 1:])))
            elif (at := next((i for i, t in enumerate(seg) if t == ":" and ":" not in seg[i - 1:i] + seg[i + 1:i + 2]), None)) is not None and names:
                # Kotlin·Rust·TypeScript·Swift 'name: Type'(이름은 ':' 바로 앞. Rust 'mut a: T'의 mut은 이름이 아니다. '::'는 경로라 이름표가 아니다)
                out.append((([t for t in seg[:at] if _NAME.fullmatch(t)] or names)[-1], "param", _type_text(seg[at + 1:])))
            elif names:  # C·C++·Java: 이름은 타입 다음의 마지막 낱말('std::vector<int>& nums', 'const string &s', 'int[] arr')
                out.append((names[-1], "param", _type_text(seg[:len(seg) - 1 - seg[::-1].index(names[-1])])))
            seg = []
        else:
            seg.append(tok)
    return out


def _declared(toks: list[str]) -> list[tuple[str, str, str]]:
    """중괄호 언어 한 줄의 선언 (이름, 꼴, 타입): 타입 꼴 뒤에 오고 그 뒤가 = ; , : 인 이름(초기값 없는 선언 포함), ':=' 왼쪽, for 머리의 반복 변수."""
    out, depth, start, typed, loop, head = [], 0, 0, None, toks[:1] == ["for"], False
    word = next((w for w in ("in", "of") if w in toks), "")
    if loop and toks[1:2] == ["("] and word:  # Kotlin·JavaScript 'for (x in xs)', 'for (const x of xs)', 'for ((i, v) in …)'
        return [(t, "loop", "") for t in toks[2:toks.index(word)] if _NAME.fullmatch(t) and t not in _LOOSE]
    for i, tok in enumerate(toks):
        if tok in ";{}":
            start, typed = i + 1, None
            head = head and tok == ";"
            continue
        if tok == "(":
            depth += 1
            if loop and i == 1:
                start, head = i + 1, True
            continue
        if tok == ")":
            depth -= 1
            continue
        if not _NAME.fullmatch(tok) or depth != (1 if head else 0):
            continue
        after = toks[i + 1] if i + 1 < len(toks) else ";"
        kind = "loop" if head else "var"
        if after == ":=":
            out.append((tok, kind, ""))
            continue
        if after not in ("=", ";", ",", ":", ")") or (after == ":" and toks[i + 2:i + 3] == [":"]):
            continue
        before = toks[start:i]
        if typed is not None and toks[i - 1:i] == [","]:
            out.append((tok, kind, typed))
            continue
        if (before and not set(before) & _NOT_TYPE and all(_TYPE_TOKEN.fullmatch(t) for t in before) and before.count("<") == before.count(">")
                and (_NAME.fullmatch(before[-1]) or before[-1] in (">", "]", "*", "&"))):
            typed = _type_text(before)
            out.append((tok, kind, typed))
    return out


def _split_top(toks: list[str]) -> list[list[str]]:
    """괄호 밖 쉼표로 나눈다."""
    parts, depth = [[]], 0
    for tok in toks:
        depth += (tok in "([{") - (tok in ")]}")
        if tok == "," and depth == 0:
            parts.append([])
        else:
            parts[-1].append(tok)
    return parts


def _rhs_after(toks: list[str], at: int) -> list[str]:
    """toks[at]('=' 등) 뒤의 식: 괄호 밖 ',' ';' 앞까지."""
    out, depth = [], 0
    for tok in toks[at + 1:]:
        if depth == 0 and tok in (",", ";"):
            break
        depth += (tok in "([{") - (tok in ")]}")
        if depth < 0:
            break
        out.append(tok)
    return out


def _go_made(toks: list[str]) -> list[tuple]:
    """Go 한 줄의 선언: 'for i, p := range xs {', 'a, b := …', 'var a, b T', 'var x = …'."""
    loop = toks[:1] == ["for"]
    if ":=" in toks:
        at = toks.index(":=")
        names = [t for t in toks[int(loop):at] if _NAME.fullmatch(t)]
        rhs = toks[at + 1:]
        if loop and "range" in rhs:
            rhs = rhs[rhs.index("range") + 1:]
            rhs = rhs[:-1] if rhs[-1:] == ["{"] else rhs
            return [(n, "loop", "", ("range", tuple(rhs), i)) for i, n in enumerate(names) if n != "_"]
        if loop:  # for i := 0; i < n; i++ {
            return [(n, "loop", "", ("for", tuple(toks[1:]))) for n in names if n != "_"]
        pieces = _split_top(_rhs_after(toks, at) if len(names) == 1 else rhs)
        return [(n, "var", "", ("=", tuple(pieces[i] if len(pieces) == len(names) else rhs), i)) for i, n in enumerate(names) if n != "_"]
    if toks[:1] == ["var"]:
        names, i = [], 1
        while i < len(toks) and _NAME.fullmatch(toks[i]):
            names.append(toks[i])
            i += 2 if toks[i + 1:i + 2] == [","] else 1
            if toks[i - 1:i] != [","]:
                break
        rest = toks[i:]
        typ = _type_text(rest[:rest.index("=")] if "=" in rest else rest)
        shape = ("=", tuple(rest[rest.index("=") + 1:])) if "=" in rest else ("type", typ)
        return [(n, "var", typ, shape) for n in names if n != "_"]
    return []


def made_statements(code: str, language: str, program: bool = False) -> list[tuple]:
    """코드(틀 줄은 뺀다)가 새로 만드는 이름 [(이름, 꼴, 타입 글, 만드는 문장), …](처음 나온 차례).
    만드는 문장: ('=', 오른쪽 식 낱말, 자리) / ('in'·':'·'range', 도는 대상, 자리) / ('for', 반복 머리) / ('type', 타입) / None(매개변수).
    짝을 '묶음의 수가 같으면 차례대로' 지으면 선언 차례를 바꾼 코드에 틀린 짝을 알렸다. 짝의 근거는 만드는 문장이다.
    Python의 풀어 받기('for a, b in xs')와 첨자 받기('for q in xs:' 뒤 'a = q[0]', 'a, b = q')는 같은 꼴('in', xs, 자리)이다.
    통째로 받는 반복 변수('for q in xs'의 q)는 자리가 없다(None)."""
    out, whole = [], {}  # whole: 통째로 받는 반복 변수 → 도는 대상
    for line in body_lines(code, language, program):
        toks = _TOKEN.findall(line)
        found = (_DEF_PY if language == "python" else _DEF).match(line)
        if found and not (language == "go" and ":=" in toks):
            at = toks.index("(", toks.index(found.group(1)))
            depth, end = 0, at
            for end in range(at, len(toks)):
                depth += (toks[end] == "(") - (toks[end] == ")")
                if depth == 0:
                    break
            out += [(*item, None) for item in _params(toks[at + 1:end], language)]
            continue
        if language == "go":
            out += _go_made(toks)
            continue
        if language != "python":
            for name, kind, typ in _declared(toks):
                i = toks.index(name)
                after = toks[i + 1] if i + 1 < len(toks) else ";"
                if after in ("=", ":="):
                    shape = ("for", tuple(toks[1:])) if kind == "loop" else ("=", tuple(_rhs_after(toks, i + 1)))
                elif after == ":" or kind == "loop":
                    rhs = toks[i + 2:]
                    shape = (":", tuple(rhs[:-2] if rhs[-2:] == [")", "{"] else rhs[:-1] if rhs[-1:] == [")"] else rhs))
                elif after in ("in", "of"):
                    shape = ("in", tuple(toks[i + 2:]))
                else:
                    shape = ("type", typ)
                out.append((name, kind, typ, shape))
            continue
        if toks[:1] == ["for"] and "in" in toks:
            targets = [t for t in toks[1:toks.index("in")] if _NAME.fullmatch(t)]
            rhs = toks[toks.index("in") + 1:]
            rhs = rhs[:-1] if rhs[-1:] == [":"] else rhs
            out += [(t, "loop", "", ("in", tuple(rhs), i if len(targets) > 1 else None)) for i, t in enumerate(targets)]
            for t in targets:  # 다시 받으면 앞 반복의 통째 값이 아니다
                whole.pop(t, None)
            if len(targets) == 1:
                whole[targets[0]] = tuple(rhs)
            continue
        names = [name for name in _first_seen([toks]) if _assigned(toks, name)]
        if names:
            depth, at = 0, None
            for i, tok in enumerate(toks):  # 'a = b = 0'은 마지막 '=' 뒤가 식이다
                depth += (tok in "([{") - (tok in ")]}")
                if depth == 0 and tok in ("=", ":="):
                    at = i
            lhs = [t for t in toks[:at] if _NAME.fullmatch(t)] if at is not None else names
            rhs = toks[at + 1:] if at is not None else []
            pieces = _split_top(rhs)
            for name in names:
                i = lhs.index(name) if name in lhs else 0
                piece = tuple(pieces[i] if len(pieces) == len(lhs) and len(lhs) > 1 else rhs)
                if piece[:1] and piece[0] in whole and len(lhs) > 1 and len(pieces) == 1 and len(piece) == 1:  # 'a, b = q'(오른쪽이 q 하나뿐)
                    out.append((name, "loop", "", ("in", whole[piece[0]], i)))
                elif piece[:1] and piece[0] in whole and len(piece) == 4 and piece[1] == "[" and piece[2].isdigit() and piece[3] == "]":  # 'a = q[0]'
                    out.append((name, "loop", "", ("in", whole[piece[0]], int(piece[2]))))
                else:
                    out.append((name, "var", "", ("=", piece, i if len(pieces) != len(lhs) else 0)))
            for name in names:  # 반복 변수에 다시 대입하면 그 뒤의 'a = q[0]'은 xs의 원소가 아니다
                whole.pop(name, None)
    seen = {}
    for item in out:
        seen.setdefault(item[0], item)
    return list(seen.values())


VAR_KINDS = ("var_from_problem", "var_during")


def shown_kind(block, language: str, program: bool = False) -> str:
    """화면에 보일 블록 종류. 변수 블록이라 했는데 그 코드가 새로 만드는 이름이 없으면(값을 돌려주거나 출력하는 블록) 꼬리표를 보이지 않는다(빈 글)."""
    return "" if block.kind in VAR_KINDS and block.reference.strip() and not made_statements(block.reference, language, program) else block.kind


def created_names(code: str, language: str, program: bool = False) -> list[tuple[str, str, str]]:
    """코드(틀 줄은 뺀다)가 새로 만드는 이름 [(이름, 꼴, 타입 글), …](처음 나온 차례). 꼴: loop(반복 변수), param(이 코드가 정의하는 함수의 매개변수), var(그 밖).
    타입 글은 중괄호 언어 선언에 적힌 타입(공백 없이. auto·var·val·let과 Python은 빈 글). 갱신(+=, 타입 없는 대입)은 만드는 것이 아니다(Python의 '='는 만드는 것).
    초기값 없는 선언('vector<int> answer;')과 도우미 함수의 매개변수를 세지 않아 짝을 짓지 못했다."""
    return [item[:3] for item in made_statements(code, language, program)]


def _assigned(toks: list[str], name: str) -> bool:
    """Python 한 줄에서 name이 '='·':='의 왼쪽(괄호 밖)에 있다(+= 같은 갱신은 아니다)."""
    depth = 0
    for i, tok in enumerate(toks):
        depth += (tok in "([{") - (tok in ")]}")
        if tok == name and depth == 0 and toks[i - 1:i] not in (["."],):
            j = i
            while toks[j + 1:j + 2] == [","] and j + 2 < len(toks) and _NAME.fullmatch(toks[j + 2]):
                j += 2
            if toks[j + 1:j + 2] in (["="], [":="]) or (toks[i + 1:i + 2] == [","] and "=" in toks and toks.index("=") > i):
                return True
    return False


def frame_of(reference: str, language: str, program: bool = False) -> dict:
    """화면이 블록 칸 코드를 이어 실행되는 파일로 만들 틀 정보. 답은 없다.
    indent: 틀 줄을 뺀 첫 줄의 들여쓰기 글자 수, head: 맨 앞에 이어지는 틀 줄(빈 줄 포함), tail: 맨 뒤에 이어지는 틀 줄,
    outer: 알맹이 줄 가운데 indent보다 얕은 앞 공백 값(오름차순. 반복·조건 안에서 시작해 그 밖에서 끝나는 블록의 바깥 단계),
    braces: 알맹이 줄의 중괄호 차(앞 블록의 반복을 닫으면 음수). 적은 코드에서 꼬리 줄을 뗄지 가르는 기준이다."""
    rows = reference.splitlines()
    skip = frame_flags(rows, language, program)
    start = next((i for i, s in enumerate(skip) if not s), len(rows))
    end = next((i for i in range(len(rows) - 1, -1, -1) if not skip[i]), start - 1) + 1
    first = rows[start] if start < len(rows) else ""
    head, tail = rows[:start], rows[max(end, start):]
    indent = _lead(first)
    return {"indent": indent, "head": head if any(row.strip() for row in head) else [], "tail": tail if any(row.strip() for row in tail) else [],
            "outer": sorted({_lead(row) for row, s in zip(rows, skip) if not s and _lead(row) < indent}),
            "braces": _brace_count(rows[start:max(end, start)]),  # 머리·꼬리 사이 전부(앞 블록의 반복을 닫는 '}'도 알맹이다)
            "tab": first.startswith("\t"),  # 계획이 탭으로 들여 썼다(Go)
            # 화면이 적은 코드 맨 앞의 틀 줄·가져오기 줄을 엔진과 같은 식으로 가른다
            "frame_re": (_FRAME_PY if language == "python" else _FRAME).pattern, "import_re": _IMPORT.pattern, "mark": "#" if language == "python" else "//"}


def plan_unit(references: list[str], language: str) -> int:
    """Python 계획의 들여쓰기 한 단계(계획 코드 전체에서 0보다 큰 가장 작은 앞 공백 수, 없으면 4). 그 밖의 언어는 0(다시 놓지 않는다).
    2칸으로 적은 블록이 4칸인 뒤 블록과 모이면 IndentationError였다."""
    if language != "python":
        return 0
    return min((_lead(row) for ref in references for row in ref.splitlines() if row.strip() and _lead(row) > 0), default=4)


def _lead(row: str) -> int:
    return len(row) - len(row.lstrip())


def _brace_count(rows: list[str]) -> int:
    return sum(row.count("{") - row.count("}") for row in rows)


def _drop_tail(lines: list[str], tail: list[str], need: int) -> list[str]:
    """화면 app.js dropTail과 같다: 적은 코드의 마지막 줄들이 tail의 앞부분과 같으면(공백 무시) 뺀다. 내 반복문을 닫는 '}'는 지우지 않는다.
    need: 뗀 뒤 남은 코드의 중괄호 차가 계획 알맹이의 차(frame_of braces)와 같을 때만 뗀다."""
    want = [row for row in tail if row.strip()]
    rows = [(re.sub(r"\s+", "", row), i) for i, row in enumerate(lines) if row.strip()]
    for k in range(min(len(want), len(rows)), 0, -1):
        last, kept = rows[-k:], lines[:rows[-k][1]]
        if all(flat == re.sub(r"\s+", "", want[j]) for j, (flat, _) in enumerate(last)) and _brace_count(kept) == need:
            while kept and not kept[-1].strip():
                kept.pop()
            return kept
    return lines


def placed(lines: list[str], indent: int, outer: list[int], unit: int = 0, tab: bool = False) -> list[str]:
    """적은 줄을 블록 자리에 놓는다(화면 app.js placed와 같다). 첫 알맹이 줄이 기준이다: 그 줄 이상 들여쓴 줄은 indent + (앞 공백 − 첫 줄),
    첫 줄보다 얕은 줄은 가까운 단계부터 계획의 바깥 단계(outer의 뒤에서부터)에 놓는다. outer가 모자라면 첫 줄과의 차만큼 내어 쓴다.
    unit > 0(Python)이면 첫 줄 이상 들여쓴 줄은 단계로 놓는다: 앞 공백 값의 쌓임 깊이 × unit(2칸·탭으로 적어도 계획의 단위로).
    반복 몸통(8칸)에서 시작해 반복 밖(4칸)에서 끝나는 블록은 가장 얕은 줄을 indent에 놓아 어떻게 적어도 바깥 줄을 놓을 수 없었다.
    tab: 계획이 탭으로 들여 쓴 언어(Go)는 앞 공백을 탭 글자로 놓는다('공백 1칸 + 탭'이 섞였다).
    한계: 괄호 안에서 이어지는 줄과 여러 줄 문자열의 줄도 단계로 다시 놓인다(실행은 같다. 여러 줄 문자열의 내용은 바뀔 수 있다)."""
    pad = "\t" if tab else " "
    rows = [row for row in lines if row.strip()]
    first = _lead(rows[0]) if rows else 0
    shallow = sorted({_lead(row) for row in rows if _lead(row) < first}, reverse=True)
    stack = [first]

    def at(row: str) -> str:
        lead = _lead(row)
        if lead < first:
            k = shallow.index(lead)
            return pad * (outer[-1 - k] if k < len(outer) else max(0, indent - (first - lead))) + row.lstrip()
        if not unit:
            return pad * indent + row[first:]
        while stack[-1] > lead:
            stack.pop()
        if stack[-1] < lead:
            stack.append(lead)
        return pad * (indent + (len(stack) - 1) * unit) + row.lstrip()

    return [at(row) if row.strip() else "" for row in lines]


# 가져오기 줄(Python import·from, Java·Kotlin·Go import, C++ #include·using namespace, Rust use, JavaScript require). 화면이 같은 식을 받아 쓴다(frame_of)
_IMPORT = re.compile(r"import\b.*|from\s+\S+\s+import\b.*|#include\b.*|using\s+namespace\b.*|use\s+.+;|(?:const|let|var)\s+.+=\s*require\(.*")


def _my_head(lines: list[str], head: list[str], language: str) -> tuple[list[str], list[str]]:
    """적은 코드 맨 앞에 이어지는 틀 줄(그 사이 빈 줄 포함. 닫는 괄호 줄은 알맹이다)을 뗀다: (머리말 맨 위에 더할 가져오기 줄, 남은 줄).
    더할 줄은 계획 머리 줄에 없는 가져오기 줄(공백 무시)뿐이고 진입 클래스·함수 머리는 버린다(계획 머리말이 넣는다).
    'import java.io.*;' + 내 class Main·main 머리를 계획 머리말 안에 통째로 넣어 컴파일 오류였다."""
    have, extra, at, cut = {re.sub(r"\s+", "", row) for row in head}, [], 0, 0
    while at < len(lines) and (not lines[at].strip() or not _plain(lines[at], language)
                               or (frame_line(lines[at], language) and not re.fullmatch(r"\s*[})]\s*;?\s*", lines[at]))):
        plain = _plain(lines[at], language)
        if plain:  # 틀 줄(그 앞의 주석·빈 줄과 함께 뗀다)
            cut = at + 1
            if _IMPORT.fullmatch(plain) and re.sub(r"\s+", "", lines[at]) not in have:
                extra.append(lines[at].strip())
        at += 1
    return extra, lines[cut:]


_ENTRY_PY = re.compile(r"def (?:solution|main)\b.*:")


def _late_entry(lines: list[str], reference: str, language: str) -> list[str]:
    """머리말이 없는 블록(Python)에 진입 함수 머리 줄을 적었으면 그 줄을 뗀다: 머리 줄은 앞 블록 자리의 틀이 이미 넣었다.
    남은 몸통은 placed가 첫 줄 기준으로 놓는다. 블록 2의 'def solution(…):'이 함수 안쪽에 겹쳐 들어갔다."""
    if language != "python" or any(_ENTRY_PY.fullmatch(_plain(row, language) or "") for row in reference.split("\n")):
        return lines
    at = next((i for i, row in enumerate(lines) if row.strip() and _plain(row, language)), None)
    if at is None or not _ENTRY_PY.fullmatch(_plain(lines[at], language)):
        return lines
    return lines[at + 1:]


def framed_parts(code: str, reference: str, language: str, program: bool = False, unit: int = 0) -> tuple[list[str], list[str], list[str], int]:
    """framed를 세 덩이로: (내 가져오기 줄 + 머리, 제자리에 놓은 내 줄, 꼬리, 내 글 앞에서 떼어 낸 줄 수). 놓은 줄은 떼고 남은 내 줄과 하나씩 맞는다."""
    frame = frame_of(reference, language, program)
    head, tail, need = frame["head"], frame["tail"], frame["braces"]
    raw = code.rstrip().split("\n")
    extra, lines = _my_head(raw, head, language) if any(row.strip() for row in head) else ([], raw)
    lines = _late_entry(lines, reference, language)
    return [*extra, *head], placed(_drop_tail(lines, tail, need), frame["indent"], frame["outer"], unit, frame["tab"]), tail, len(raw) - len(lines)


def framed(code: str, reference: str, language: str, program: bool = False, unit: int = 0) -> str:
    """블록 칸에 적은 코드를 그 블록 자리에 들어갈 코드로(화면 app.js composed와 같은 규칙): 내 가져오기 줄 + head + 제자리에 놓은 코드(placed) + tail.
    머리말이 있는 블록은 적은 코드 맨 앞의 틀 줄을 떼어 낸다(_my_head). unit: 계획의 들여쓰기 한 단계(plan_unit)."""
    before, body, after, _ = framed_parts(code, reference, language, program, unit)
    return "\n".join([*before, *body, *after])


# 언어마다 이름을 바꾸지 않는 글: 문자열·문자 글자(s), 주석(c). 문자 글자는 한 글자(또는 '\' 한 벌)뿐이라 Rust의 수명 표기 'a는 문자열이 아니다
_DQ, _SQ, _CHAR = r'"(?:\\.|[^"\\\n])*"', r"'(?:\\.|[^'\\\n])*'", r"'(?:\\.[^'\n]*?|[^'\\\n])'"
_NOTE = r"//[^\n]*|/\*[\s\S]*?\*/"
_LEXED = {
    "python": (r"(?<!\w)[rRbBuUfF]{0,2}(?:\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|" + _DQ + "|" + _SQ + ")", r"#[^\n]*"),
    "javascript": (r"`(?:\\[\s\S]|[^`\\])*`|" + _DQ + "|" + _SQ, _NOTE),
    "kotlin": (r'"""[\s\S]*?"""|' + _DQ + "|" + _CHAR, _NOTE),
    "java": (r'"""[\s\S]*?"""|' + _DQ + "|" + _CHAR, _NOTE),
    "rust": (r'(?<!\w)b?r#*"[\s\S]*?"#*|(?<!\w)b?"(?:\\[\s\S]|[^"\\])*"|(?<!\w)b?' + _CHAR, _NOTE),
    "go": (r"`[^`]*`|" + _DQ + "|" + _CHAR, _NOTE),
    "cpp": (r'(?<!\w)(?:u8|[uUL])?R"\([\s\S]*?\)"|(?<!\w)(?:u8|[uUL])?' + _DQ + "|" + _CHAR, _NOTE),
}
_LEX = {lang: re.compile(rf"(?P<s>{s})|(?P<c>{c})|(?P<n>[A-Za-z_]\w*)|(?P<d>\d\w*)|(?P<o>[()\[\]{{}}])") for lang, (s, c) in _LEXED.items()}
_KEYWORD = re.compile(r"\s*=(?!=)")  # 이름 뒤의 '='(==가 아니다)
_WORD = re.compile(r"(?<![\w.])[A-Za-z_]\w*")
_MEMBER = {"cpp": ("->", "::"), "java": ("::",), "kotlin": ("::",), "rust": ("::",)}  # 이 앞에 오는 이름은 멤버·경로다(Python의 '[::k]'는 변수라 뺀다. Java·Kotlin의 '->'는 람다라 뺀다)


def swap_names(code: str, names: dict[str, str], language: str) -> str:
    """이름 바꾸기 {계획 이름: 사용자 이름}. 이름인 자리만 바꾼다(언어의 문법으로 가른다):
    점 뒤 이름(속성·메서드), C++의 '->' 뒤와 C++·Java·Kotlin·Rust의 '::' 뒤 이름(멤버·경로), 문자열·문자 글자, Python·Kotlin의 키워드 인자 이름(호출 괄호 안의 '이름=')은 그대로 둔다.
    문자열 안에서는 끼워 넣기 자리만 바꾼다: Python f-문자열의 {…}, Kotlin의 $이름·${…}, JavaScript 백틱의 ${…}.
    주석 안의 낱말은 바꾼다(돌지 않는 글이라 코드와 같은 이름으로 읽히게. 주석 안의 따옴표는 문자열로 보지 않는다)."""
    if not names:
        return code
    out, at, stack, recent = [], 0, [], []
    for m in _LEX.get(language, _LEX["cpp"]).finditer(code):
        out.append(code[at:m.start()])
        at, text, kind = m.end(), m.group(0), m.lastgroup
        if kind == "s":
            text = _filled(text, names, language)
        elif kind == "c":
            text = _WORD.sub(lambda word: names.get(word.group(0), word.group(0)), text)
        elif kind == "n" and text in names and code[m.start() - 1:m.start()] != "." and code[m.start() - 2:m.start()] not in _MEMBER.get(language, ()) and not (
                language in ("python", "kotlin") and stack[-1:] == ["("] and _KEYWORD.match(code, m.end())):
            text = names[text]
        elif kind == "o" and text in "([{":
            stack.append("def" if text == "(" and recent[-2:-1] == ["def"] else text)  # def 머리의 '이름=기본값'은 매개변수다
        elif kind == "o" and stack:
            stack.pop()
        if kind in "ndo":
            recent = [*recent[-1:], m.group(0)]
        out.append(text)
    return "".join(out + [code[at:]])


def _filled(text: str, names: dict[str, str], language: str) -> str:
    """문자열 글자 하나. 끼워 넣기가 있는 문자열이면 그 자리만 바꾼다. 나머지는 글자 그대로다(이름과 같은 낱말이 값으로 쓰인다)."""
    if language == "python":
        pre = re.match(r"[A-Za-z]*", text).group(0)
        if "f" not in pre.lower():
            return text
        quote = 3 if text[len(pre):len(pre) + 3] in ('"""', "'''") else 1
    elif (language == "kotlin" and text.startswith('"')) or (language == "javascript" and text.startswith("`")):
        pre, quote = "", 3 if text.startswith('"""') else 1
    else:
        return text
    head, tail = len(pre) + quote, len(text) - quote
    return text[:head] + _holes(text[head:tail], names, language) + text[tail:]


def _holes(body: str, names: dict[str, str], language: str) -> str:
    """문자열 안의 끼워 넣기 자리만 바꾼다. Python은 {…}({{·}}는 글자), Kotlin은 $이름과 ${…}, JavaScript는 ${…}('\\'로 막은 글자는 그대로)."""
    out, i = [], 0
    while i < len(body):
        if (language != "python" and body[i] == "\\") or (language == "python" and body[i:i + 2] in ("{{", "}}")):
            out.append(body[i:i + 2])
            i += 2
            continue
        lead = "{" if language == "python" else "${"
        if body.startswith(lead, i):
            end = _close(body, i + len(lead) - 1)
            if end < 0:
                out.append(body[i:])
                break
            inner = body[i + len(lead):end]
            out.append(lead + (_py_field(inner, names) if language == "python" else swap_names(inner, names, language)) + "}")
            i = end + 1
            continue
        word = re.compile(r"\$([A-Za-z_]\w*)").match(body, i) if language == "kotlin" else None
        if word:
            out.append("$" + names.get(word.group(1), word.group(1)))
            i = word.end()
            continue
        out.append(body[i])
        i += 1
    return "".join(out)


def _close(text: str, at: int) -> int:
    """text[at]의 '{'와 짝인 '}'의 자리(없으면 -1)."""
    depth = 0
    for j in range(at, len(text)):
        depth += (text[j] == "{") - (text[j] == "}")
        if depth == 0:
            return j
    return -1


def _py_field(inner: str, names: dict[str, str]) -> str:
    """f-문자열의 {…} 안. 식은 맨 바깥의 ':'·'!'(변환) 앞까지이고, 그 뒤 서식 안의 {…}도 자리다. '{x=}'는 식의 글자가 출력에 나와 그대로 둔다."""
    depth, cut = 0, len(inner)
    for j, ch in enumerate(inner):
        depth += (ch in "([{") - (ch in ")]}")
        if depth == 0 and (ch == ":" or (ch == "!" and inner[j + 1:j + 2] != "=")):
            cut = j
            break
    expr, rest = inner[:cut], inner[cut:]
    shown = re.search(r"(?<![=!<>])=\s*$", expr)
    return (expr if shown else swap_names(expr, names, "python")) + _holes(rest, names, "python")


def pairs_of(reference: str, code: str, pairs: list[list[str]], language: str, program: bool = False) -> dict[str, str]:
    """통과한 사용자 블록이 내놓는 이름 짝 {계획 이름: 내 이름}: 이 블록이 대입한 계획 이름을 내 코드가 그대로 쓰면 그 이름 자신(앞 블록의 예전 짝을 끝낸다),
    그리고 저장된 짝(pairs: [[내 이름, 계획 이름], …])."""
    # 내 코드도 그 이름을 만들 때만 그 이름 자신이다('next_arrival = arrivals[time][0]'의 time은 읽기만 했는데 앞 블록의 바꾼 짝을 끝냈다)
    mine = {name for name, _, _ in created_names(code, language, program)}
    return {**{name: name for name, _, _ in created_names(reference, language, program) if name in mine}, **{plan: my for my, plan in pairs}}


def name_tables(count: int, pairs: dict[int, dict[str, str]], scopes: list = ()) -> list[dict[str, str]]:
    """블록 자리마다의 이름 바꾸기 표: 블록 i에는 i보다 앞 블록들의 짝(pairs)을 블록 차례로 합친 것(뒤 블록이 같은 계획 이름을 덮는다).
    scopes: [(함수가 끝나는 블록, 그 함수 안에서만 사는 계획 이름)]. 함수가 끝난 뒤 블록의 표에서는 그 이름의 짝을 뺀다(함수 이름의 짝은 남는다).
    표가 문제 전체에 하나라 계획이 다른 반복에서 다시 쓴 이름(name)에 앞 블록의 짝(r)이 쓰였다.
    도우미 함수의 매개변수 짝(n → rows)이 solution(n, m, k)에까지 쓰였다."""
    tables, table = [], {}
    for i in range(count):
        tables.append(dict(table))
        table = {**table, **pairs.get(i, {})}
        # 함수가 이 블록에서 끝나면 그때까지 쌓인 그 이름의 짝을 뺀다(뒤 블록이 같은 이름을 새로 짝지으면 그 짝은 남는다).
        # 한계: 한 블록에서 도우미가 끝나고 다음 함수가 같은 이름으로 시작하면 그 블록의 새 짝도 빠진다. 줄 단위 범위가 필요해지면 그때 나눈다
        gone = {name for end, names in scopes if end == i for name in names}
        table = {k: v for k, v in table.items() if k not in gone}
    return tables


def scoped_names(references: list[str], language: str, program: bool = False) -> list[tuple[int, set[str]]]:
    """도우미 함수(진입 함수가 아닌 함수)마다 (끝나는 블록, 그 함수의 매개변수와 몸통에서 만든 이름). 안쪽 함수는 그 안쪽 함수의 것만."""
    rows, owner = [], []
    for i, ref in enumerate(references):
        for row in ref.split("\n"):
            rows.append(row)
            owner.append(i)
    out = []
    for at, row in enumerate(rows):
        plain = _plain(row, language)
        found = (_DEF_PY if language == "python" else _DEF).match(plain) if plain and not frame_line(row, language) else None
        if not found or (language == "python" and not plain.startswith("def ")):
            continue
        end = at
        if language == "python":  # def 줄의 들여쓰기로 돌아오는 줄 앞까지
            for k in range(at + 1, len(rows)):
                if not (rows[k].strip() and _plain(rows[k], language)):
                    continue  # 빈 줄·주석 줄은 끝을 정하지 않는다(다음 블록 맨 앞의 빈 줄을 함수 안으로 세면 그 블록까지 짝이 남았다)
                if _lead(rows[k]) <= _lead(row):
                    break
                end = k
        else:  # 닫는 중괄호까지
            depth = 0
            for k in range(at, len(rows)):
                cut = _NOT_BRACE.sub("", rows[k])
                depth += cut.count("{") - cut.count("}")
                end = k
                if depth <= 0 and k > at or (k == at and "{" in cut and depth == 0):
                    break
        body = "\n".join(rows[at:end + 1])
        names = {n for n, kind, *_ in made_statements(body, language, program)}
        if found.group(1) not in ("solution", "main") and names:
            out.append((owner[end], names - {found.group(1)}))
    return out


def composed_parts(blocks, codes: dict, language: str, names: list | None = None, program: bool = False, starter: str = "", trusted: bool = True) -> list[list]:
    """블록 칸의 글을 실행되는 한 파일의 조각으로 [[블록 순번, 글], …](글이 빈 블록은 없다). 블록 코드 확인이 잇는 것과 같은 framed를 쓴다.
    조각마다 알맹이 첫 줄 위에 블록 주석을 그 줄의 들여쓰기로 넣는다. names: 블록마다 보여 줄 이름(없으면 종류). program: 문항이 표준 입출력 방식이다.
    trusted가 거짓이면(튜터의 풀이를 확인하지 못했다) 계획 코드의 틀을 믿지 않고 시작 코드(starter)의 틀 안에 내 블록을 차례로 놓는다:
    블록마다 내 글 맨 앞의 틀 줄(진입 머리·가져오기)을 떼고(_my_head. 뗀 가져오기는 맨 위로), 끝 블록에서 시작 코드의 꼬리와 같은 줄을 떼어(_drop_tail)
    첫 블록에 머리, 끝 블록에 꼬리만 단다. 떼지 않아 머리가 두 번, 닫는 괄호가 두 벌 들어갔다.
    시작 코드의 가져오기 줄은 맨 앞 가져오기 줄들 뒤에 더한다. 화면의 모으기와 엔진의 이어 붙이기가 따로 구현되어 블록 2에 적은 def가 확인에서는 떼이고 모을 때는 안쪽에 들어갔다."""
    refs = [b.reference for b in blocks]
    unit = plan_unit(refs, language)
    mark = "#" if language == "python" else "//"
    items = [(i, ((codes.get(block.id) or {}).get("code") or "").rstrip()) for i, block in enumerate(blocks)]
    items = [(i, code) for i, code in items if code.strip()]
    frame = frame_of(starter, language, program) if not trusted and starter.strip() else None
    if frame is not None:
        extra, bodies = [], []
        for _, code in items:
            more, lines = _my_head(code.split("\n"), frame["head"], language) if frame["head"] else ([], code.split("\n"))
            extra += [row for row in more if row not in extra]
            bodies.append(lines)
        if bodies:  # 끝 블록의 꼬리: 앞 블록들이 열어 둔 괄호까지 세어, 남은 글이 시작 코드의 알맹이와 같은 괄호 차일 때만 뗀다
            bodies[-1] = _drop_tail(bodies[-1], frame["tail"], frame["braces"] - sum(_brace_count(lines) for lines in bodies[:-1]))
    out = []
    for n, (i, code) in enumerate(items):
        if frame is not None:
            lines = placed(bodies[n], frame["indent"], frame["outer"], 0, frame["tab"])
            lines = [*(extra + frame["head"] if n == 0 else []), *lines, *(frame["tail"] if n == len(items) - 1 else [])]
        else:
            lines = framed(code, refs[i], language, program, unit).split("\n") if refs[i].strip() else code.split("\n")
        at = next((k for k, row in enumerate(lines) if row.strip() and _plain(row, language) and not frame_line(row, language)), 0)
        label = f"{mark} 블록 {i + 1} · {(names or [None] * len(blocks))[i] or blocks[i].kind}"
        lines.insert(at, re.match(r"\s*", lines[at]).group(0) + label if lines else label)
        out.append([i, "\n".join(lines)])
    if out and (lead := starter_imports([row for _, text in out for row in text.split("\n")], starter, language)):
        rows = out[0][1].split("\n")
        at = import_end(rows, language)
        out[0][1] = "\n".join([*rows[:at], *lead, *rows[at:]])
    return out


_DEF_PY = re.compile(r"def ([A-Za-z_]\w*)\s*\(")
_DEF = re.compile(r"(?!(?:if|for|while|switch|else|catch|return|do|try)\b)[\w<>\[\]:,&*\s]*?\b([A-Za-z_]\w*)\s*\([^;{}]*\)[^;{}()=]*\{")


def defined_function(code: str, language: str, program: bool = False) -> str:
    """코드가 함수 하나를 정의하면 그 이름(틀 줄인 진입 함수는 뺀다). 없거나 여럿이면 빈 글."""
    found = [m.group(1) for line in body_lines(code, language, program) if (m := (_DEF_PY if language == "python" else _DEF).match(line))]
    return found[0] if len(found) == 1 else ""


_START_IMPORT = ("python", "java", "kotlin", "cpp")  # 같은 가져오기를 두 번 적어도 오류가 아닌 언어(Go는 안 쓴 가져오기, Rust는 같은 이름의 두 번 가져오기, JavaScript는 같은 이름의 두 번 선언이 오류다)


def starter_imports(rows: list[str], starter: str, language: str) -> list[str]:
    """시작 코드의 가져오기 줄 가운데 rows에 아직 없는 것. 시작 코드의 'import java.util.*;'를 믿고 쓴 코드가 이어 붙인 프로그램에서도 돌게 한다."""
    if language not in _START_IMPORT:
        return []
    have, out = {re.sub(r"\s+", "", row) for row in rows}, []
    for row in (starter or "").splitlines():
        flat = re.sub(r"\s+", "", row)
        if _IMPORT.fullmatch(_plain(row, language) or "") and flat not in have:
            have.add(flat)
            out.append(row.strip())
    return out


def import_end(rows: list[str], language: str) -> int:
    """맨 앞 가져오기 줄(그 사이 빈 줄·주석 포함) 가운데 마지막 줄의 바로 뒤 자리(없으면 0). 시작 코드에서 더하는 가져오기 줄은 여기에 넣는다.
    맨 위에 놓은 'using namespace std;'가 '#include' 앞에 와 GCC에서 오류였고, Python 'from __future__' 앞에 놓인 줄은 SyntaxError다."""
    at = 0
    for i, row in enumerate(rows):
        plain = _plain(row, language)
        if not plain:
            continue
        if not _IMPORT.fullmatch(plain):
            break
        at = i + 1
    return at


def spliced_view(references: list[str], index: int, code: str, language: str, mine: dict[int, str] | None = None,
                 tables: list[dict[str, str]] | None = None, program: bool = False, starter: str = "", own_only: bool = False) -> tuple[str, list[dict]]:
    """블록 코드 확인의 실행 프로그램과, 그 프로그램의 줄이 누구의 것인지: index 블록은 사용자가 방금 적은 코드, mine에 있는 블록은 사용자가 적어 둔 코드,
    나머지는 풀이 가이드의 블록 reference에 그 자리의 이름 바꾸기 표(tables[i]: {계획 이름: 사용자 이름})를 적용한 것(앞 블록에서 내 이름을 쓰면 NameError였다).
    own_only면 나머지 블록은 틀(머리·꼬리)만 두고 알맹이를 뺀다(내 블록만 이은 프로그램). program: 문항이 표준 입출력 방식이다(서버가 아는 문항의 방식).
    spans: [{"first", "last"(프로그램의 1부터 센 줄), "block", "whose": this|mine|tutor, "cut"(내 글 앞에서 떼어 낸 줄 수), "code"(내 글)}]. 틀과 가져오기 줄은 tutor 쪽이다."""
    mine, unit = {**(mine or {}), index: code}, plan_unit(references, language)
    rows, spans = [], []

    def add(lines: list[str], block: int, whose: str, cut: int = 0, text: str = "") -> None:
        spans.append({"first": len(rows) + 1, "last": len(rows) + len(lines), "block": block, "whose": whose, "cut": cut, "code": text})
        rows.extend(lines)

    for i, ref in enumerate(references):
        if i in mine:
            before, body, after, cut = framed_parts(mine[i], ref, language, program, unit)
            add(before, i, "tutor")
            add(body, i, "this" if i == index else "mine", cut, mine[i])
            add(after, i, "tutor")
        elif own_only:
            frame = frame_of(ref, language, program)
            add([*frame["head"], *frame["tail"]], i, "tutor")
        else:
            add(swap_names(ref, tables[i] if tables else {}, language).split("\n"), i, "tutor")
    lead, at = starter_imports(rows, starter, language), import_end(rows, language)
    for item in spans:  # 넣은 자리 뒤의 줄 번호만 밀린다
        item["first"] += len(lead) if item["first"] > at else 0
        item["last"] += len(lead) if item["last"] > at else 0
    return "\n".join([*rows[:at], *lead, *rows[at:]]), spans


def spliced(references: list[str], index: int, code: str, language: str, mine: dict[int, str] | None = None,
            tables: list[dict[str, str]] | None = None, program: bool = False, starter: str = "", own_only: bool = False) -> str:
    return spliced_view(references, index, code, language, mine, tables, program, starter, own_only)[0]


def entry_params(code: str, language: str) -> list[str] | None:
    """진입 함수 solution 머리의 매개변수 이름(차례대로). 머리가 여러 줄이어도 괄호가 닫힐 때까지 읽는다. 머리를 찾지 못하거나 괄호가 닫히지 않으면 None."""
    rows = [_plain(line, language) for line in (code or "").splitlines()]
    for i, row in enumerate(rows):
        if "solution" not in row:
            continue
        plain = "\n".join(rows[i:])
        found = (_DEF_PY if language == "python" else _DEF).match(plain)
        if found and found.group(1) == "solution":
            toks = _TOKEN.findall(plain)
            at = toks.index("(", toks.index("solution"))
            depth = 0
            for end in range(at, len(toks)):
                depth += (toks[end] == "(") - (toks[end] == ")")
                if depth == 0:
                    return [name for name, *_ in _params(toks[at + 1:end], language)]
            return None
    return None
