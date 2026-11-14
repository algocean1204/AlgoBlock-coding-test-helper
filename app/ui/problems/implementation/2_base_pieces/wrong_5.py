# 틀린 까닭: 값이 같은 자리에서도 끊는다(앞 자리보다 작아질 때만 끊어야 한다)
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
        if DIGITS.index(text[i]) <= DIGITS.index(text[i - 1]):
            pieces.append(text[i])
        else:
            pieces[-1] += text[i]
    return [len(pieces), max(read_base(piece, base) for piece in pieces)]
