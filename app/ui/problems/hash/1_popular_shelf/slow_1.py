# 느린 까닭: 기록마다 그때까지의 기록을 처음부터 다시 세어 본다(기록이 10만 개면 10만 × 10만 번)
def solution(loans, k):
    shelf = []
    for i in range(len(loans)):
        if loans[:i + 1].count(loans[i]) == k:
            shelf.append(loans[i])
    return shelf
