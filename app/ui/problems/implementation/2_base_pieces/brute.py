def solution(base, reading):
    # 가장 큰 자리부터: base의 거듭제곱을 몇 번 뺄 수 있는지로 자리값을 정한다(solution.py는 나머지를 모아 뒤집는다)
    power = 1
    while power * base <= reading:
        power *= base
    values = []
    while power > 0:
        digit = 0
        while reading >= power:
            reading -= power
            digit += 1
        values.append(digit)
        power //= base

    # 끊는 위치를 먼저 모두 찾은 뒤 잘라, 조각마다 파이썬 int(글, base)로 읽는다
    text = "".join("0123456789ABCDEF"[v] for v in values)
    cuts = [0] + [i for i in range(1, len(values)) if values[i] < values[i - 1]] + [len(values)]
    pieces = [text[cuts[j]:cuts[j + 1]] for j in range(len(cuts) - 1)]
    return [len(pieces), max(int(piece, base) for piece in pieces)]
