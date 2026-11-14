def solution(classes, medals):
    # 정렬하지 않는다. 반마다 '나보다 앞서는 반의 수'를 세면 그것이 내 자리(0부터)다
    def ahead(i, j):  # i반이 j반보다 앞서는가: 규칙 1~4를 위에서부터 차례로 본다
        for rule in range(3):
            if medals[i][rule] != medals[j][rule]:
                return medals[i][rule] > medals[j][rule]
        return classes[i] < classes[j]

    n = len(classes)
    answer = [""] * n
    for i in range(n):
        place = 0
        for j in range(n):
            if j != i and ahead(j, i):
                place += 1
        answer[place] = classes[i]
    return answer
