# 틀린 까닭: range(low, high)로 돌려 high를 대 보지 않는다
def solution(apples, pears, low, high):
    best_size = low
    best_left = apples + pears + 1
    for size in range(low, high):
        left = apples % size + pears % size
        if left <= best_left:
            best_size = size
            best_left = left
    return [best_size, apples // best_size + pears // best_size]
