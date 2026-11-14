# 틀린 까닭: 사과와 배를 합친 수로 남는 과일을 센다(섞어 담을 수 없다)
def solution(apples, pears, low, high):
    best_size = low
    best_left = apples + pears + 1
    for size in range(low, high + 1):
        left = (apples + pears) % size
        if left <= best_left:
            best_size = size
            best_left = left
    return [best_size, apples // best_size + pears // best_size]
