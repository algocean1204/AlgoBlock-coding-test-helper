# 틀린 까닭: 조각을 base진법이 아니라 10진법으로 읽는다(A~F가 든 조각은 읽지도 못한다)
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
    return [len(pieces), max(int(piece) for piece in pieces)]
