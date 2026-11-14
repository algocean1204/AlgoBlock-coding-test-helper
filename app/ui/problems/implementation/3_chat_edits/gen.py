LARGE = 2

LOWER = "abcdefghijklmnopqrstuvwxyz"


def take(rng, items):
    """목록에서 아무거나 하나를 꺼낸다(맨 뒤와 바꿔 꺼내므로 빠르다)."""
    index = rng.randint(0, len(items) - 1)
    items[index], items[-1] = items[-1], items[index]
    return items.pop()


def walk(rng, length, senders, words, weights):
    """올바른 기록을 length개 만든다. weights = (SEND, EDIT, DELETE)의 비중. 번호는 보낸 순서와 관계없이 고른다."""
    numbers = rng.distinct(1, 999_999, length)
    alive, out = [], []
    for _ in range(length):
        send, edit, delete = weights
        kind = rng.choice(["SEND"] * send + (["EDIT"] * edit + ["DELETE"] * delete if alive else []) or ["SEND"])
        if kind == "SEND":
            number = str(numbers.pop())
            alive.append(number)
            out.append(f"SEND {number} {rng.choice(senders)} {rng.choice(words)}")
        elif kind == "EDIT":
            out.append(f"EDIT {rng.choice(alive)} {rng.choice(words)}")
        else:
            out.append(f"DELETE {take(rng, alive)}")
    return out


def small(rng):
    cases = [
        [["SEND 1 a b"]],  # 가장 짧은 기록
        [["SEND 1 a b", "DELETE 1"]],  # 모두 지워진다: 빈 배열
        [["SEND 7 ann x", "EDIT 7 x"]],  # 같은 내용으로 고쳐도 *
        [["SEND 7 ann x", "EDIT 7 y", "EDIT 7 z"]],  # 마지막 고친 내용
        [["SEND 1 ann p", "SEND 2 bob q", "SEND 3 ann r", "SEND 4 bob s", "DELETE 2", "DELETE 3"]],  # 지운 뒤에 bob 둘이 붙는다
        [["SEND 1 ann p", "SEND 2 bob q", "SEND 3 ann r"]],  # 이어지지 않으면 묶지 않는다
        [["SEND 9 cy a", "SEND 8 cy b", "SEND 7 cy c", "EDIT 8 bb"]],  # 한 줄 가운데 메시지만 고친다
        [["SEND 999999 abcdefgh abcdefgh", "SEND 1 abcdefgh zzzzzzzz", "EDIT 999999 h"]],  # 가장 긴 보낸이·내용, 큰 번호
        [["SEND 5 a x", "SEND 4 b y", "DELETE 5", "SEND 3 b z", "SEND 2 a w", "DELETE 4", "DELETE 3"]],
        [["SEND 1 x x", "SEND 2 x x", "EDIT 2 x", "SEND 3 y x", "EDIT 1 y"]],  # 보낸이와 내용이 같은 글자
        [["SEND 12 ann a", "SEND 3 ann b", "DELETE 12", "SEND 45 ann c", "EDIT 45 d", "DELETE 3", "SEND 6 bob e"]],
        [["SEND 10 a m", "SEND 20 b m", "EDIT 10 n", "EDIT 20 n", "DELETE 10", "DELETE 20", "SEND 30 c o"]],
    ]
    cases.append([walk(rng, 40, ["ann", "bob"], ["hi", "ok", "yo"], (3, 2, 1))])
    for _ in range(4):
        cases.append([walk(rng, rng.randint(10, 50), ["ann", "bob", "cy"], ["hi", "ok", "yo", "go"], (rng.randint(2, 4), rng.randint(0, 3), rng.randint(0, 2)))])
    return cases


def random_small(rng):
    return [walk(rng, rng.randint(1, 12), ["a", "b", "c"], ["x", "y", "z"], (3, rng.randint(0, 2), rng.randint(0, 2)))]


def valid(records):
    if not 1 <= len(records) <= 60_000:
        return False
    sent, alive = set(), set()
    for record in records:
        words = record.split(" ")
        size = {"SEND": 4, "EDIT": 3, "DELETE": 2}.get(words[0])
        if size is None or len(words) != size:
            return False
        number = words[1]
        if not (number.isdigit() and number[0] != "0" and 1 <= int(number) <= 999_999):
            return False
        if any(not (1 <= len(word) <= 8 and all(ch in LOWER for ch in word)) for word in words[2:]):
            return False
        if words[0] == "SEND":
            if number in sent:
                return False
            sent.add(number)
            alive.add(number)
        elif number not in alive:
            return False
        elif words[0] == "DELETE":
            alive.discard(number)
    return True


def names(rng, count, low, high):
    return sorted({rng.word(rng.randint(low, high)) for _ in range(count)})


def large(rng, index):
    if index == 0:  # 보내기·고치기·지우기가 고루 섞인다
        return [walk(rng, 60_000, names(rng, 3, 2, 4), names(rng, 500, 2, 5), (4, 5, 1))]
    # 앞의 2만 개로 메시지를 쌓은 뒤, 뒤의 4만 개는 모두 고치기와 지우기
    head = walk(rng, 20_000, names(rng, 4, 2, 4), names(rng, 500, 2, 5), (1, 0, 0))
    alive = [record.split(" ")[1] for record in head]
    words = names(rng, 500, 2, 5)
    tail = []
    for _ in range(40_000):
        if rng.chance(1, 8) and len(alive) > 1:
            tail.append(f"DELETE {take(rng, alive)}")
        else:
            tail.append(f"EDIT {rng.choice(alive)} {rng.choice(words)}")
    return [head + tail]
