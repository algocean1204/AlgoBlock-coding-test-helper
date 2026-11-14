# 느린 까닭: 합칠 때마다 남은 눈덩이 전체에서 가장 가벼운 것을 찾아 지운다(20만 개면 20만 × 20만 번에 가깝다)
def solution(snowballs):
    balls = list(snowballs)
    total = 0
    while len(balls) > 1:
        lightest = min(balls)
        balls.remove(lightest)
        second = min(balls)
        balls.remove(second)
        merged = lightest + second
        total += merged
        balls.append(merged)
    return total
