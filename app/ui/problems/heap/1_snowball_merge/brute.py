def solution(snowballs):
    balls = list(snowballs)
    total = 0
    while len(balls) > 1:
        balls.sort()
        merged = balls[0] + balls[1]
        total += merged
        balls = balls[2:] + [merged]
    return total
