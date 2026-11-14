# 틀린 까닭: 10 이상인 자리값을 글자(A~F)가 아니라 수 그대로("10", "11") 이어 써서, 한 자리가 두 글자가 된다
DIGITS = "0123456789ABCDEF"


def read_base(text, base):
    value = 0
    for ch in text:
        value = value * base + DIGITS.index(ch)
    return value


def solution(base, reading):
    text = ""
    while reading > 0:
        text = str(reading % base) + text
        reading //= base
    pieces = [text[0]]
    for i in range(1, len(text)):
        if DIGITS.index(text[i]) < DIGITS.index(text[i - 1]):
            pieces.append(text[i])
        else:
            pieces[-1] += text[i]
    return [len(pieces), max(read_base(piece, base) for piece in pieces)]
