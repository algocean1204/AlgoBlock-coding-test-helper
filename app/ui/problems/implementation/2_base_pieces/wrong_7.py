# 틀린 까닭: 가장 큰 조각을 수가 아니라 글자로 견주어 고른다("9"가 "12"보다 크게 나온다)
DIGITS = "0123456789ABCDEF"


def read_base(text, base):
    value = 0
    for ch in text:
        value = value * base + DIGITS.index(ch)
    return value


def solution(base, reading):
    text = ""
    while reading > 0:
        text = DIGITS[reading % base] + text
        reading //= base
    pieces = [text[0]]
    for i in range(1, len(text)):
        if DIGITS.index(text[i]) < DIGITS.index(text[i - 1]):
            pieces.append(text[i])
        else:
            pieces[-1] += text[i]
    return [len(pieces), read_base(max(pieces), base)]
