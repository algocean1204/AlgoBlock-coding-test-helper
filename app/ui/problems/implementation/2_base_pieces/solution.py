DIGITS = "0123456789ABCDEF"


def to_base(reading, base):
    # 나머지를 끝 자리부터 모은 뒤 뒤집는다
    reversed_digits = ""
    while reading > 0:
        reversed_digits += DIGITS[reading % base]
        reading //= base
    return reversed_digits[::-1]


def read_base(text, base):
    # 앞자리부터 값 = 값 × base + 자리값
    value = 0
    for ch in text:
        value = value * base + DIGITS.index(ch)
    return value


def solution(base, reading):
    text = to_base(reading, base)

    # 앞 자리보다 작아지는 곳에서 새 조각을 시작한다
    pieces = [text[0]]
    for i in range(1, len(text)):
        if DIGITS.index(text[i]) < DIGITS.index(text[i - 1]):
            pieces.append(text[i])
        else:
            pieces[-1] += text[i]

    largest = 0
    for piece in pieces:
        value = read_base(piece, base)
        if value > largest:
            largest = value
    return [len(pieces), largest]
