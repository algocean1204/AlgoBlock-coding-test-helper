LARGE = 1


def small(rng):
    # 예시(1, 3, 4)를 뺀 2 ~ 20 전부. 1, 2일 때 칸이 모자라는 실수와 3부터 갈라지는 실수를 모두 본다
    return [[2]] + [[n] for n in range(5, 21)]


def medium(rng):
    # 36은 답이 int에 들고(2,082,876,103) 37부터 int를 넘는다. 1,000,000,007로 나누는 실수도 여기서 드러난다
    return [[36], [37], [45], [59]]


def random_small(rng):
    return [rng.randint(1, 16)]


def valid(n):
    return 1 <= n <= 60


def large(rng, index):
    return [60]  # 답이 int를 넘고(2^53보다는 작다), 메모 없는 재귀는 끝나지 않는다
