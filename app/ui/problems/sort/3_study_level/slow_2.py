# 느린 까닭: x를 회원 수부터 하나씩 줄이며 매번 전체를 다시 센다(답이 작으면 거의 20만 × 20만 번)
def solution(solved):
    for x in range(len(solved), -1, -1):
        count = 0
        for value in solved:
            if value >= x:
                count += 1
        if count >= x:
            return x
