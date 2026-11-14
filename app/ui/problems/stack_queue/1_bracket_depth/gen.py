LARGE = 2
CLOSE = {"(": ")", "[": "]", "{": "}"}


def balanced(rng, pairs, letters, deep):
    """괄호 쌍 pairs개로 올바른 문자열을 만든다. deep이 클수록 더 겹겹이 싼다. letters의 글자를 사이사이에 섞는다."""
    out, stack, left = [], [], pairs
    while left or stack:
        if left and (not stack or rng.chance(deep, 10)):
            ch = rng.choice("([{")
            stack.append(ch)
            left -= 1
            out.append(ch)
        else:
            out.append(CLOSE[stack.pop()])
        if letters and rng.chance(1, 3):
            out.append(rng.choice(letters))
    return "".join(out)


def broken(rng, text):
    """괄호 하나를 지우거나, 종류를 바꾸거나, 이웃한 둘을 맞바꾸거나, 여는 괄호 하나를 끼워 넣는다."""
    spots = [i for i, ch in enumerate(text) if ch in "()[]{}"]
    kind = rng.randint(0, 3)
    if len(spots) < 2 or kind == 0:
        at = rng.randint(0, len(text))
        return text[:at] + rng.choice("([{") + text[at:]
    i = rng.choice(spots)
    if kind == 1:
        return text[:i] + text[i + 1:]
    if kind == 2:
        side = "([{" if text[i] in "([{" else ")]}"
        return text[:i] + rng.choice([ch for ch in side if ch != text[i]]) + text[i + 1:]
    k = spots.index(i)
    j = spots[k + 1] if k + 1 < len(spots) else spots[k - 1]
    a, b = min(i, j), max(i, j)
    return text[:a] + text[b] + text[a + 1:b] + text[a] + text[b + 1:]


def valid(expr):
    return 1 <= len(expr) <= 200_000 and all(ch in "abcdefghijklmnopqrstuvwxyz()[]{}" for ch in expr)


def small(rng):
    cases = [
        ["a"], ["()"], ["(]"], [")("], ["]"], ["(("], ["{[()]}"], ["()[]{}"],
        ["x{(})y"], ["ab[cd(ef)gh]ij{k}"], ["((a)[b]{c})"], ["{{{{{{{{{{}}}}}}}}}}"],
        ["z(y[x{w}v]u)t)"], ["(()(()))"],  # 닫았다 다시 열어도 깊이는 이어진다
    ]
    cases.append([balanced(rng, 120, "abc", 6)])
    cases.append([broken(rng, balanced(rng, 120, "abc", 6))])
    deep = balanced(rng, 300, "", 10)
    cases.append([deep])
    cases.append([deep[:-1] + ("]" if deep[-1] != "]" else ")")])  # 맨 끝 하나만 엇갈린다
    while len(cases) < 20:
        text = balanced(rng, rng.randint(3, 12), "pq", rng.randint(3, 8))
        if rng.chance(1, 2):
            text = broken(rng, text)
        if [text] not in cases:
            cases.append([text])
    return cases


def random_small(rng):
    text = balanced(rng, rng.randint(0, 5), "ab", rng.randint(3, 8))
    if text == "" or rng.chance(1, 2):
        text = broken(rng, text) if text else rng.choice(["a", "b", "ab"])
    return [text]


def large(rng, index):
    opens = [rng.choice("([{") for _ in range(100_000)]
    closes = [CLOSE[ch] for ch in reversed(opens)]
    if index == 1:  # 맨 바깥 쌍만 엇갈린다: 끝까지 봐야 안다
        closes[-1] = ")" if opens[0] != "(" else "]"
    return ["".join(opens) + "".join(closes)]
