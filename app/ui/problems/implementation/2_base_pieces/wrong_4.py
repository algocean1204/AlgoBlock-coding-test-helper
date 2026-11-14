# 틀린 까닭: 'reading이 base보다 작아질 때까지' 나누어 맨 앞자리를 빠뜨린다(몫이 0이 될 때까지 나눠야 한다)
DIGITS = "0123456789ABCDEF"


def read_base(text, base):
    value = 0
    for ch in text:
        value = value * base + DIGITS.index(ch)
    return value


def solution(base, reading):
    text = ""
    while reading >= base:
        text = DIGITS[reading % base] + text
        reading //= base
    if text == "":
        text = DIGITS[reading]
    pieces = [text[0]]
    for i in range(1, len(text)):
        if DIGITS.index(text[i]) < DIGITS.index(text[i - 1]):
            pieces.append(text[i])
        else:
            pieces[-1] += text[i]
    return [len(pieces), max(read_base(piece, base) for piece in pieces)]
