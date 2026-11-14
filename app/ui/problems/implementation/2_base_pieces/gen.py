LARGE = 0

MAX_READING = 10 ** 14


def random_reading(rng, digits):
    """자릿수가 고르게 퍼지도록: 먼저 자릿수를 고르고 그 안에서 값을 고른다."""
    size = rng.randint(1, digits)
    return rng.randint(10 ** (size - 1), 10 ** size - 1)


def small(rng):
    cases = [
        [2, 1],  # 가장 작은 reading: "1" 한 조각
        [2, 2],  # "10": 0에서 끊는다
        [16, 15],  # "F": 글자 자리 하나
        [10, 1000],  # "1000": 0이 이어져도 한 번만 끊는다. 10의 거듭제곱(자릿수를 log로 구하면 실수 오차)
        [3, 3 ** 5],  # "100000"
        [10, 9876543210],  # 자리마다 작아진다: 조각 10개
        [10, 1123456789],  # 작아지지 않는다: 조각 하나 = reading
        [10, 12345678999999],  # 조각 하나가 int를 넘는다
        [10, 912],  # "9"와 "12": 글자로 견주면 "9"가 크다
        [10, 5555],  # 같은 자리만: 끊지 않는다
        [2, MAX_READING],  # 가장 큰 reading, 가장 작은 base
        [16, MAX_READING],  # 가장 큰 reading, 가장 큰 base
        [2, 2 ** 31],  # int를 넘는 reading
        [16, int("FEDCBA98765", 16)],  # 글자 자리끼리 작아진다
        [16, int("9A9B0C", 16)],  # 9 다음 A: 글자 표의 위치로 견준다
        [16, int("1A2B3C4D5E6F", 16)],
        [7, int("6543210", 7)],
        [11, int("12A0A", 11)],  # A(10)이 자리 하나
    ]
    for _ in range(2):
        cases.append([rng.randint(2, 16), random_reading(rng, 14)])
    return cases


def random_small(rng):
    return [rng.randint(2, 16), random_reading(rng, 7)]


def valid(base, reading):
    return isinstance(base, int) and isinstance(reading, int) and 2 <= base <= 16 and 1 <= reading <= MAX_READING


def large(rng, index):
    return []
