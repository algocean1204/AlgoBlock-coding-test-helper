"""블록 코드 확인의 이름 짝. 계획 블록이 '내놓는 이름'(뒤 블록이 읽는 이름)을 사용자 코드의 어느 이름이 맡는지,
그 짝이 굳었는지(알려도 되는지)를 만드는 문장의 꼴로 가른다.

굳은 짝: 계획 이름과 내 이름의 만드는 문장 꼴이 같고 그 꼴이 양쪽에 하나씩뿐(또는 굳은 짝을 다 지은 뒤 같은 (꼴 갈래, 타입) 묶음에 하나씩 남음).
바꿔도 되는 무리: 같은 꼴의 이름이 양쪽에 둘 이상('n = 0', 'i = 0' ↔ 'light = 0', 'boxes = 0'). 나온 차례를 첫 가정으로만 쓴다(굳지 않음).
묶음의 수가 같으면 차례대로 '확실'하게 짝지어 선언 차례를 바꾼 코드에 틀린 짝을 알리고 뒤 블록에 거짓 오답을 말했다."""

import re
from dataclasses import dataclass, field

from ..common.solution import _NAME, _TOKEN, body_lines, made_statements, name_candidates

_MUTATE = ("sort", "append", "extend", "insert", "pop", "remove", "clear", "add", "update", "setdefault", "appendleft", "popleft", "reverse",
           "push_back", "pop_back", "push", "emplace", "emplace_back", "put", "offer", "poll", "discard")


def writes(code: str, language: str, program: bool = False) -> list[str]:
    """코드가 쓰는 이름(새로 만듦, 대입, 증감 대입, 값을 바꾸는 메서드 호출, 칸 대입, ++·--, 제자리 정렬)을 처음 나온 차례로."""
    out = [name for name, *_ in made_statements(code, language, program)]
    for line in body_lines(code, language, program):
        toks = _TOKEN.findall(line)
        typed = _typed(toks)
        if typed:
            out += [toks[i] for i in typed[0]]
        for i, tok in enumerate(toks):
            if not _NAME.fullmatch(tok) or toks[i - 1:i] in (["."], ["::"]) or (typed and i in typed[1]):
                continue
            after = toks[i + 1] if i + 1 < len(toks) else ""
            if after in ("=", "+=", "-=", "*=", "/=", "//=", "%=", "**=", "&=", "|=", "^=", "<<=", ">>=", ":=") and toks[i + 2:i + 3] != ["="]:
                out.append(tok)
            elif after == "." and toks[i + 2:i + 3] and toks[i + 2] in _MUTATE and toks[i + 3:i + 4] == ["("]:
                out.append(tok)
            elif after == "[":  # 칸 대입 x[i] = …, x[i] += …, x[i]++
                depth, j = 0, i + 1
                while j < len(toks):
                    depth += (toks[j] == "[") - (toks[j] == "]")
                    j += 1
                    if depth == 0 and toks[j:j + 1] != ["["]:
                        break
                if toks[j:j + 1] and (toks[j] in ("=", "+=", "-=", "*=", "/=", "%=", "|=", "&=", "^=") or toks[j:j + 2] in (["+", "+"], ["-", "-"])):
                    out.append(tok)
            elif toks[i + 1:i + 3] in (["+", "+"], ["-", "-"]) or (i >= 2 and toks[i - 2:i] in (["+", "+"], ["-", "-"])):
                out.append(tok)
        text = " ".join(toks)
        for pattern in (r"\bsort \( (\w+) \. begin", r"\bArrays \. sort \( (\w+)", r"\bsort \. (?:Ints|Strings|Float64s|Slice) \( (\w+)", r"\breverse \( (\w+) \. begin"):
            out += re.findall(pattern, text)
    return list(dict.fromkeys(out))


def _typed(toks: list[str]) -> tuple[list[int], range] | None:
    """'val|var|let|const [mut] 이름[, 이름…] … =' 선언 줄이면 (선언한 이름의 자리, 이름 뒤부터 '=' 앞까지 = 형의 자리). 아니면 None.
    Kotlin·Rust·Swift의 '이름: 형 ='과 Go의 '이름 형 ='이 같은 문법이다('&str', '[3]int', '*Node', 'map[string]int'). 이름이 없으면('let [a, b] =') 선언으로 보지 않는다."""
    if toks[:1] not in (["val"], ["var"], ["let"], ["const"]) or "=" not in toks:
        return None
    start = at = 1 + (toks[1:2] == ["mut"])
    while at < len(toks) and _NAME.fullmatch(toks[at]):
        at += 1
        if toks[at:at + 1] != [","]:
            break
        at += 1
    names = [i for i in range(start, at) if _NAME.fullmatch(toks[i])]
    return (names, range(at, toks.index("="))) if names else None


def _shape(item: tuple, fresh: set[str], back: dict[str, str]) -> tuple | None:
    """만드는 문장의 꼴: 이 블록이 만드는 이름은 '#', 앞에서 온 이름은 계획 쪽 이름으로."""
    name, kind, typ, shape = item
    if shape is None:
        return None
    tag, *rest = shape
    toks = rest[0] if rest and isinstance(rest[0], tuple) else ()
    norm = tuple("#" if t in fresh else back.get(t, t) for t in toks)
    return (kind, tag, norm, *rest[1:]) if tag != "type" else (kind, "type", typ)


@dataclass
class Pairing:
    emitted: list[str]  # 계획이 내놓는 이름(뒤 블록의 계획 코드가 읽는다)
    open: list[str]  # 그 가운데 사용자가 (이 자리의 표의 이름으로) 쓰지 않는 것
    fixed: dict = field(default_factory=dict)  # 굳은 짝 {계획 이름: 내 이름}
    groups: list = field(default_factory=list)  # 바꿔도 되는 무리 [(계획 이름들, 내 이름들)] 나온 차례
    candidates: dict = field(default_factory=dict)  # 그 밖의 이름 {계획 이름: [후보…]}(굳지 않음)
    orphans: list = field(default_factory=list)  # 짝도 없고 이 블록에서 다시 읽히지 않는 내 새 이름
    omitted: bool = False  # 쓰지 않는 이름이 남았는데 짝 없는 내 새 이름이 없다(갱신을 빠뜨렸다)
    params: list = field(default_factory=list)  # 계획 매개변수 차례(굳지 않았거나 차례가 다를 때만)
    own: dict = field(default_factory=dict)  # 계획 이름을 그대로 쓴 것 {N: N}

    def guess(self) -> dict:
        """첫 가정: 굳은 짝 + 무리는 나온 차례 + 그 밖은 겹치지 않는 첫 후보."""
        table, used = dict(self.fixed), set(self.fixed.values())
        for plans, mine in self.groups:
            for p, m in zip(plans, mine):
                table[p] = m
                used.add(m)
        for name, cands in self.candidates.items():
            pick = next((c for c in cands if c not in used), None)
            if pick is not None:
                table[name] = pick
                used.add(pick)
        return table

    def settled(self) -> bool:
        """이 블록의 짝이 모두 굳었다(무리·후보·매개변수 문제가 없다)."""
        return not self.groups and not self.candidates and not self.params


def pair_block(reference: str, code: str, table: dict[str, str], later: str, earlier: set[str], language: str, program: bool = False,
               loose: list = (), before: list = ()) -> Pairing:
    """블록 하나의 짝. table: 이 자리의 이름 바꾸기 표 {계획 이름: 내 이름}, later: 뒤 블록의 계획 코드, earlier: 앞 블록의 계획이 만든 이름,
    loose: 앞 블록의 굳지 않은 무리 [(계획 이름들, 내 이름들)]. 그 이름은 만드는 문장의 꼴에서 무리 표시로 본다(굳지 않은 짝으로 굳은 짝을 짓지 않는다).
    before: 앞 블록에서 내가 미리 만들었고 아직 짝이 없는 이름의 만드는 문장. 이 블록의 이름으로 모자랄 때만 무리·후보에 넣는다(굳은 짝으로 짓지 않는다)."""
    read_later = set(re.findall(r"[A-Za-z_]\w*", later))
    plan_made = made_statements(reference, language, program)
    plan_names = {item[0] for item in plan_made}
    fresh_plan = {n for n, kind, *_ in plan_made if n not in earlier or kind in ("loop", "param")}
    emitted = [n for n in writes(reference, language, program) if n in read_later]
    mine_writes, typed = set(writes(code, language, program)), set(re.findall(r"[A-Za-z_]\w*", code))
    open_names = [n for n in emitted if table.get(n, n) not in mine_writes and n not in mine_writes]
    # 계획 이름을 그대로 쓴 것. 내놓는 이름을 읽기만 했으면('ps = sorted(prices)'의 prices) 그대로 쓴 것이 아니다
    own = {n: n for n in plan_names | set(emitted) if n in typed and n not in table and n not in open_names}
    mine_made = made_statements(code, language, program)
    paired_mine = set(table.values()) | (plan_names & typed) | set(earlier & typed)
    new_mine = [item for item in mine_made if item[0] not in paired_mine]
    # 계획 블록은 쓰지 않는데 내가 고쳐 쓰는 이름('items.sort()'의 items)도 짝 후보다('order = sorted(items)' 자리)
    plan_writes = set(writes(reference, language, program))
    # 단 앞에서 있던 이름(계획 코드에 나오는 이름)만: 'coutn += 1'처럼 어디서도 만든 적 없는 이름은 후보가 아니다
    known = set(re.findall(r"[A-Za-z_]\w*", reference + "\n" + later))
    rewritten = [n for n in mine_writes if n not in plan_writes and n not in {m[0] for m in mine_made} and n not in paired_mine - (earlier & typed)
                 and n not in table.values() and n in known]
    result = Pairing(emitted, open_names, own=own)
    # 매개변수: 계획 이름을 그대로 쓴 것의 자리가 다르면 차례가 다르다. 이름이 달라도 하나뿐이거나 타입으로 하나씩 갈리면 굳은 짝,
    # 갈리지 않는 둘 이상은 자리를 첫 가정으로 하는 무리다(굳지 않음. 뒤 블록이 함수 몸통을 이어 쓰면 이름이 필요하다)
    plan_params = [item for item in plan_made if item[1] == "param"]
    mine_params = [item for item in mine_made if item[1] == "param"]
    if plan_params and mine_params:
        names_p, names_m = [p[0] for p in plan_params], [m[0] for m in mine_params]
        same = [n for n in names_p if n in names_m]
        if len(names_p) != len(names_m) or any(names_p.index(n) != names_m.index(n) for n in same):
            result.params = names_p
        else:
            types_p, types_m = [p[2] for p in plan_params], [m[2] for m in mine_params]
            by_type = all(types_p) and len(set(types_p)) == len(types_p) and sorted(types_p) == sorted(types_m)
            differ = [(p, m) for p, m in zip(plan_params, mine_params) if p[0] != m[0]]
            if by_type and types_p != types_m:  # 타입으로 갈리는데 자리가 다르다: 뒤 블록이 부르는 차례와 다르다
                result.params = names_p
            elif len(differ) == 1 or by_type:
                for p, m in differ:
                    result.fixed[p[0]] = next(x[0] for x in mine_params if x[2] == p[2]) if by_type else m[0]
            elif differ:  # 자리로 짐작한 무리일 뿐 차례가 다르다는 근거는 없다. 돌린 결과와 그 가정을 말한다(HOLD_PARAMS가 아니다)
                result.groups.append(([p[0] for p, _ in differ], [m[0] for _, m in differ]))
    back = {mine: plan for plan, mine in table.items()}
    plan_mark = {}
    for gi, (plans, mines) in enumerate(loose):
        plan_mark.update({p: f"?{gi}" for p in plans})
        back.update({m: f"?{gi}" for m in mines})
    # 계획 이름을 그대로 쓴 것도 꼴이 같은 이름이 있으면 바꿔도 되는 무리다('total = 0', 'acc = 0' ↔ 'total = 0', 'count = 0'). '그대로'는 첫 가정일 뿐이다
    # (계획의 total을 내 답 변수로 쓰자 남은 count와 내 새 이름 하나를 굳은 짝으로 알리고 거짓 오답을 말했다)
    mine_names = {m[0] for m in mine_made}
    own_made = [item for item in plan_made if item[0] in own and item[0] in fresh_plan and item[0] in mine_names and item[1] != "param"]
    if own_made:
        all_p = {item[0]: _shape(item, fresh_plan, plan_mark) for item in plan_made if item[0] in fresh_plan and item[1] != "param"}
        all_m = {item[0]: _shape(item, mine_names, back) for item in mine_made if item[1] != "param" and (item[0] in own or item[0] not in paired_mine)}
        for item in own_made:
            shape = all_p.get(item[0])
            plans = [n for n, sp in all_p.items() if sp == shape and shape is not None]
            mine = [m for m, sm in all_m.items() if sm == shape]
            if len(plans) >= 2 and len(plans) == len(mine) and not any(item[0] in g[0] for g in result.groups):
                rest = iter([m for m in mine if m not in plans])
                order = [p if p in mine else next(rest) for p in plans]  # 그대로 쓴 이름은 제 이름을 첫 가정으로
                result.groups.append((plans, order))
                for n in plans:
                    result.own.pop(n, None)
                    if n not in result.open and n in read_later:
                        result.open.append(n)
    grouped_p = {p for plans, _ in result.groups for p in plans}
    grouped_m = {m for _, mine in result.groups for m in mine}
    open_names = [n for n in open_names if n not in grouped_p]
    if not open_names:
        return result
    new_names = [item[0] for item in new_mine if item[1] != "param" and item[0] not in grouped_m] + rewritten
    if not new_names and not result.groups:
        result.omitted = True  # 갱신을 빠뜨렸다: 앞에서 온 표 그대로 돌린 결과가 내 코드의 일이다
        return result
    plan_items = [item for item in plan_made if item[0] in fresh_plan and item[1] != "param" and item[0] not in typed and item[0] not in grouped_p]
    mine_items = [item for item in new_mine if item[1] != "param" and item[0] not in grouped_m]
    shape_p = {item[0]: _shape(item, fresh_plan, plan_mark) for item in plan_items}
    shape_m = {item[0]: _shape(item, {m[0] for m in mine_made}, back) for item in mine_items}
    # 앞에서 온 이름을 바꾸는 줄('prices = sorted(prices)', 'prices.sort()'): 그 이름을 읽어 만든 내 새 이름이 후보다
    rebind = [n for n in open_names if n not in shape_p]
    plan_rebind = {}
    for line in body_lines(reference, language, program):
        toks = _TOKEN.findall(line)
        if toks[:1] and toks[0] in rebind and toks[1:2] == ["="]:
            plan_rebind[toks[0]] = (("var", "=", tuple(toks[2:]), 0))
    taken = set()
    for name in open_names:
        if name in shape_p or name not in plan_rebind:
            continue
        hits = [m for m, s in shape_m.items() if s == plan_rebind[name]]
        if len(hits) == 1:
            result.fixed[name] = hits[0]
            taken.add(hits[0])
    # 굳은 짝: 꼴이 같고 그 꼴이 양쪽에 하나씩뿐
    by_shape_p, by_shape_m = {}, {}
    for n, s in shape_p.items():
        by_shape_p.setdefault(s, []).append(n)
    for m, s in shape_m.items():
        if m not in taken:
            by_shape_m.setdefault(s, []).append(m)
    for s, plans in by_shape_p.items():
        mine = by_shape_m.get(s, [])
        if s is None or not mine:
            continue
        if len(plans) == 1 and len(mine) == 1:
            result.fixed[plans[0]] = mine[0]
        elif len(plans) == len(mine):
            result.groups.append((plans, mine))
    done_p = set(result.fixed) | {p for plans, _ in result.groups for p in plans}
    done_m = set(result.fixed.values()) | {m for _, mine in result.groups for m in mine}
    # 남은 것: 같은 (꼴 갈래, 타입) 묶음에 하나씩 남으면 굳은 짝. 남은 내 새 이름이 남은 계획 이름보다 많으면 어느 것이 짝인지 모른다
    # ('for idx in range(…): g = returned[idx]'에서 idx를 반복 변수 name의 짝으로 굳히면 거짓 오답이다)
    left_p = [item for item in plan_items if item[0] not in done_p]
    left_m = [item for item in mine_items if item[0] not in done_m]
    for item in list(left_p) if len(left_m) + len(rewritten) <= len(left_p) else []:
        same_p = [p for p in left_p if p[1:3] == item[1:3]]
        same_m = [m for m in left_m if m[1:3] == item[1:3]]
        if len(same_p) == 1 and len(same_m) == 1:
            result.fixed[item[0]] = same_m[0][0]
            left_p.remove(item)
            left_m.remove(same_m[0])
    done_p = set(result.fixed) | {p for plans, _ in result.groups for p in plans}
    done_m = set(result.fixed.values()) | {m for _, mine in result.groups for m in mine}
    # 앞 블록에서 미리 만든 내 이름: 같은 꼴의 남은 계획 이름 수와 (앞 이름 + 이 블록의 남은 이름) 수가 같으면 나온 차례대로 무리(굳지 않음)
    early = [item for item in before if item[0] not in done_m and item[0] not in table.values() and item[0] not in typed]
    if early:
        shape_e = {item[0]: _shape(item, {e[0] for e in early}, back) for item in early}
        left_p = [item for item in left_p if item[0] not in done_p]
        for s in dict.fromkeys(shape_p[p[0]] for p in left_p):
            plans = [p[0] for p in left_p if shape_p[p[0]] == s]
            mine = [e for e, se in shape_e.items() if se == s] + [m[0] for m in left_m if m[0] not in done_m and shape_m.get(m[0]) == s]
            if s is not None and len(plans) >= 2 and len(plans) == len(mine) and any(e in mine for e in shape_e):
                result.groups.append((plans, mine))
        done_p = set(result.fixed) | {p for plans, _ in result.groups for p in plans}
        done_m = set(result.fixed.values()) | {m for _, mine in result.groups for m in mine}
    words = set(re.findall(r"[A-Za-z_]\w*", reference + "\n" + later))
    for name in open_names:
        if name in done_p or name in own:
            continue
        item = next((p for p in plan_made if p[0] == name), (name, "var", "", None))
        fits = [m for m in left_m + early if m[0] not in done_m and not (m[2] and item[2] and m[2] != item[2])]
        same = [m[0] for m in fits if m[1:3] == item[1:3]]
        others = [m[0] for m in fits if m[0] not in same] + [n for n in rewritten if n not in done_m]
        rest = [c for c in name_candidates(code, reference, language, name, words, program)
                if c not in done_m and c not in table.values() and c not in plan_names and c not in {m[0] for m in mine_made if m[2] and item[2] and m[2] != item[2]}]
        cands = list(dict.fromkeys(same + others + rest))
        if cands:
            result.candidates[name] = cands
    paired = set(result.guess().values())
    counts = {}
    for tok in _TOKEN.findall("\n".join(body_lines(code, language, program))):
        counts[tok] = counts.get(tok, 0) + 1
    result.orphans = [m[0] for m in mine_items if m[0] not in paired and counts.get(m[0], 0) <= 1]
    return result
