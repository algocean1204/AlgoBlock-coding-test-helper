# 틀린 까닭: 나머지를 나온 순서대로 이어 붙이고 뒤집지 않아, 자리가 거꾸로 된 글을 쪼갠다
DIGITS = "0123456789ABCDEF"


def read_base(text, base):
    value = 0
    for ch in text:
        value = value * base + DIGITS.index(ch)
    return value


def solution(base, reading):
    text = ""
    while reading > 0:
        text += DIGITS[reading % base]
        reading //= base
    pieces = [text[0]]
    for i in range(1, len(text)):
        if DIGITS.index(text[i]) < DIGITS.index(text[i - 1]):
            pieces.append(text[i])
        else:
            pieces[-1] += text[i]
    return [len(pieces), max(read_base(piece, base) for piece in pieces)]
