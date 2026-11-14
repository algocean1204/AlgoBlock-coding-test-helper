# 틀린 까닭: 끊은 곳의 자리를 앞 조각의 끝에 붙이고, 그다음 자리부터 새 조각을 시작한다
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
    start_next = False
    for i in range(1, len(text)):
        if start_next:
            pieces.append(text[i])
            start_next = False
        else:
            pieces[-1] += text[i]
        if DIGITS.index(text[i]) < DIGITS.index(text[i - 1]):
            start_next = True
    return [len(pieces), max(read_base(piece, base) for piece in pieces)]
