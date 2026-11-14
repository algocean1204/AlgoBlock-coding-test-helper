def solution(solved):
    # 정렬하지 않는다. x마다 'x문제 이상 푼 회원'을 직접 센다.
    # x명 이상이 되려면 x는 회원 수 이하이므로 x는 0부터 회원 수까지만 보면 된다
    best = 0
    for x in range(len(solved) + 1):
        count = 0
        for value in solved:
            if value >= x:
                count += 1
        if count >= x:
            best = x
    return best
