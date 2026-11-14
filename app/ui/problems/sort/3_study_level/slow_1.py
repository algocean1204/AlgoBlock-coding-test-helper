# 느린 까닭: x를 0부터 하나씩 늘리며 매번 전체를 다시 센다(답이 10만이면 10만 × 20만 번)
def solution(solved):
    x = 0
    while True:
        count = 0
        for value in solved:
            if value >= x + 1:
                count += 1
        if count >= x + 1:
            x += 1
        else:
            return x
