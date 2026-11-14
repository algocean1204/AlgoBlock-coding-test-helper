def solution(road, t):
    # 자동차 위치를 집합으로 들고 t초를 1초씩 그대로 따라간다
    n = len(road)
    cars = {i for i, ch in enumerate(road) if ch == '>'}
    total = 0
    for _ in range(t):
        moved = set()
        for car in cars:
            front = (car + 1) % n
            if front in cars:
                moved.add(car)
            else:
                moved.add(front)
                if car == n - 1:
                    total += 1
        cars = moved
    return total
