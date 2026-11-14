def solution(apples, pears, low, high):
    best_size = low
    best_left = apples + pears + 1  # 어떤 size보다도 많이 남는 값에서 시작한다
    for size in range(low, high + 1):  # 상자 크기를 하나씩 대 본다
        left = apples % size + pears % size  # 사과와 배는 섞지 않으므로 따로 남는다
        if left <= best_left:  # 같을 때도 바꾸면 더 큰 size가 남는다
            best_size = size
            best_left = left
    return [best_size, apples // best_size + pears // best_size]
