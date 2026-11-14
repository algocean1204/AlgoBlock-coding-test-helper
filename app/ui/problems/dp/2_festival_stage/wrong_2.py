# 틀린 까닭: 사례금이 큰 날부터 욕심내어 고르고, 이웃한 날이 이미 골라졌으면 건너뛴다
def solution(pay):
    n = len(pay)
    chosen = [False] * n
    order = sorted(range(n), key=lambda day: -pay[day])
    total = 0
    for day in order:
        if day > 0 and chosen[day - 1]:
            continue
        if day < n - 1 and chosen[day + 1]:
            continue
        chosen[day] = True
        total += pay[day]
    return total
