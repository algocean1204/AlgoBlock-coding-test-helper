# 틀린 까닭: 남는 과일 수가 같을 때 바꾸지 않아 작은 size를 고른다
def solution(apples, pears, low, high):
    best_size = low
    best_left = apples + pears + 1
    for size in range(low, high + 1):
        left = apples % size + pears % size
        if left < best_left:
            best_size = size
            best_left = left
    return [best_size, apples // best_size + pears // best_size]
