LARGE = 0

CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.,!?'&:"
SKIP = ["a", "an", "the", "of", "and"]


def base(title):
    """규칙 1~4까지 만든 글(taken에 겹치는 이름을 넣으려고 쓴다)."""
    words = ["".join(ch for ch in word.lower() if ch.isalnum()) for word in title.split()]
    words = [word for word in words if word]
    left = [word for word in words if word not in SKIP]
    words = left or words
    slug = words[0][:24]
    for word in words[1:]:
        if len(slug) + 1 + len(word) > 24:
            break
        slug += "-" + word
    return slug


def small(rng):
    cases = [
        ["a", []],  # 가장 짧은 제목: 규칙 3의 낱말 하나뿐이라 빼지 않는다
        ["Z", ["z"]],  # 대문자 하나, 겹침
        ["Hello   World", []],  # 이어진 빈칸
        ["  The  End  ", []],  # 양 끝 빈칸, the를 뺀다
        ["THE QUICK FOX", ["quick-fox"]],  # 소문자로 바꾼 뒤에야 the를 뺀다
        ["Of, And: The!", []],  # 다듬은 뒤에야 규칙 3의 낱말이 된다. 모두 빠지면 빼지 않는다
        ["Tips & Tricks", ["tips-tricks", "tips-tricks-2", "tips-tricks-3", "tips-tricks-5"]],  # -4에서 멈춘다
        ["Abcdefghijklmnopqrstuvwxyz Day", []],  # 첫 낱말이 24글자보다 길다
        ["abcdefghijklmnopqrstuvwx yz", ["abcdefghijklmnopqrstuvwx"]],  # 첫 낱말이 꼭 24글자, 겹치면 길이를 넘어도 된다
        ["abcd efgh ijkl mnop qrst", []],  # 이으면 꼭 24글자: 붙인다
        ["abcd efgh ijkl mnop qrstu vw", []],  # 24글자를 넘는 낱말에서 멈추면 뒤의 짧은 낱말도 붙이지 않는다
        ["e-mail & co.uk 2024", ["email-couk-2024", "email-couk-2024-2"]],  # 빼기와 점도 지운다
        ["It's a Dog's Life", []],
        ["x y z", ["x-y-z-2"]],  # -2는 없고 기본 이름은 비어 있다
        ["A Tale of Two Cities and a Long Walk Home", ["tale-two-cities-long-walk"]],
        ["1 2 3 4 5 6 7 8 9 10 11 12 13", []],
    ]
    for _ in range(3):
        title = rng.word(rng.randint(10, 80), CHARS)
        if not any(ch.isalnum() for ch in title):
            title += "q"
        cases.append([title, []])
    return cases


WORDS = ["a", "The", "of", "AND", "an,", "Big", "cat!", "x", "yy", "&", "--", "Q7", "abcdefghij", "zz:z"]


def random_small(rng):
    count = rng.randint(1, 8)
    title = " ".join(rng.choice(WORDS) for _ in range(count))
    if rng.chance(1, 4):
        title = " " + title + "  "
    if not any(ch.isalnum() for ch in title):
        title += " Ok"
    slug = base(title)
    taken = []
    if rng.chance(2, 3):  # 기본 이름과 그 뒤 번호 몇 개를 겹치게 둔다
        taken.append(slug)
        for number in range(2, 2 + rng.randint(0, 4)):
            if rng.chance(3, 4):
                taken.append(f"{slug}-{number}")
    taken += ["big-cat", "x-yy", "q7"]
    return [title, sorted(set(taken))]


def valid(title, taken):
    if not (isinstance(title, str) and 1 <= len(title) <= 80 and all(ch in CHARS for ch in title) and any(ch.isalnum() for ch in title)):
        return False
    if not (0 <= len(taken) <= 30 and len(set(taken)) == len(taken)):
        return False
    return all(1 <= len(name) <= 30 and all(ch in "abcdefghijklmnopqrstuvwxyz0123456789-" for ch in name) for name in taken)


def large(rng, index):
    return []
