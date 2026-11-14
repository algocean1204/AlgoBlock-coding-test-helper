# 틀린 까닭: 상자의 수를 사과와 배를 합친 수로 나눠 센다
def solution(apples, pears, low, high):
    best_size = low
    best_left = apples + pears + 1
    for size in range(low, high + 1):
        left = apples % size + pears % size
        if left <= best_left:
            best_size = size
            best_left = left
    return [best_size, (apples + pears) // best_size]
