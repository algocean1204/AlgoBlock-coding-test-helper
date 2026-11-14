LARGE = 2

LOWER = "abcdefghijklmnopqrstuvwxyz"


def names(rng, count, length):
    """길이 length의 서로 다른 이름 count개."""
    out, seen = [], set()
    while len(out) < count:
        name = rng.word(length)
        if name not in seen:
            seen.add(name)
            out.append(name)
    return out


def random_log(rng, length, zones, kinds, top):
    """구역 zones와 종 kinds로 기록과 질문을 섞은 장부. 마릿수는 0~top이며 0이 자주 나온다."""
    log = []
    for _ in range(length):
        pick = rng.randint(1, 10)
        if pick <= 6:
            n = 0 if rng.chance(1, 3) else rng.randint(1, top)
            log.append(f"see {rng.choice(zones)} {rng.choice(kinds)} {n}")
        elif pick <= 8:
            log.append(f"zone {rng.choice(zones)}")
        else:
            log.append(f"kind {rng.choice(kinds)}")
    if not any(line.split()[0] != "see" for line in log):
        log.append(f"kind {rng.choice(kinds)}")
    return log


def small(rng):
    cases = [
        [["zone a"]],  # 가장 짧은 장부: 아무것도 없다
        [["kind a"]],
        [["see a b 1", "zone a", "kind b"]],
        [["see a b 0", "zone a", "kind b"]],  # 0마리로만 적힌 종
        [["see x y 2", "see x y 3", "see x y 7", "kind y", "zone x"]],  # 다시 세어도 한 곳·한 종
        [["see x y 2", "see x y 0", "see x y 0", "see x y 0", "kind y", "see z y 1", "kind y"]],  # 0을 거듭 적기
        [["see p q 5", "see p q 0", "see p q 4", "kind q", "zone p"]],  # 사라졌다 다시 나타난다
        [["see a b 1", "see b a 1", "zone a", "kind a", "zone b", "kind b", "zone c", "kind c"]],  # 구역 이름과 종 이름은 따로
        [["see m s 1", "see n s 1", "see o s 1", "kind s", "see n s 0", "kind s", "zone n", "zone m"]],
        [["see abcdefgh hgfedcba 1000", "zone abcdefgh", "kind hgfedcba", "kind abcdefgh"]],  # 가장 긴 이름, 가장 큰 수
        [["see w a 1", "see w b 2", "see w c 3", "zone w", "see w b 0", "zone w", "see w a 9", "zone w", "see w c 0", "see w a 0", "zone w"]],
        [["kind f", "see g f 3", "see h f 0", "kind f", "see h f 2", "kind f", "see g f 1", "kind f"]],
        [["see see zone 1", "see zone kind 2", "zone see", "kind zone", "zone zone", "kind kind", "kind see"]],  # 명령과 같은 글자의 이름
    ]
    for _ in range(6):
        zones = names(rng, rng.randint(1, 4), rng.randint(1, 2))
        kinds = names(rng, rng.randint(1, 5), rng.randint(1, 2))
        cases.append([random_log(rng, rng.randint(15, 60), zones, kinds, 1000)])
    return cases


def random_small(rng):
    zones = names(rng, rng.randint(1, 3), 1)
    kinds = names(rng, rng.randint(1, 3), 1)
    return [random_log(rng, rng.randint(1, 12), zones, kinds, 3)]


def valid(log):
    if not (1 <= len(log) <= 70_000):
        return False
    asked = False
    for line in log:
        words = line.split(" ")
        if words[0] == "see" and len(words) == 4:
            if not (words[3].isdigit() and 0 <= int(words[3]) <= 1000 and str(int(words[3])) == words[3]):
                return False
            names_ = words[1:3]
        elif words[0] in ("zone", "kind") and len(words) == 2:
            asked = True
            names_ = words[1:]
        else:
            return False
        if any(not (1 <= len(name) <= 8 and all(ch in LOWER for ch in name)) for name in names_):
            return False
    return asked


def large(rng, index):
    if index == 0:  # 구역 3만 5천 곳 뒤에 종 질문 3만 5천 개: 질문마다 구역을 모두 훑는 풀이가 가장 오래 걸린다
        zones = names(rng, 35_000, 6)
        kinds = names(rng, 40, 5)
        log = [f"see {zone} {rng.choice(kinds)} {rng.randint(0, 1000)}" for zone in zones]
        log += [f"kind {rng.choice(kinds)}" for _ in range(35_000)]
        return [log]
    # 한 구역에 종 3만 가지 뒤에 그 구역 질문이 많다: 질문마다 그 구역의 종을 모두 훑는 풀이가 가장 오래 걸린다
    kinds = names(rng, 30_000, 6)
    log = [f"see marsh {kind} {rng.randint(1, 1000)}" for kind in kinds]
    while len(log) < 70_000:
        if rng.chance(1, 10):
            log.append(f"see marsh {rng.choice(kinds)} {rng.randint(0, 2)}")
        else:
            log.append("zone marsh")
    return [log]
