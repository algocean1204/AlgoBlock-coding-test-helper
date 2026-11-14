def solution(classes, medals):
    rows = []
    for i in range(len(classes)):
        gold, silver, bronze = medals[i]
        # 메달은 많은 쪽이 앞(내림차순)이라 마이너스를 붙이고, 이름은 사전 순(오름차순) 그대로 둔다
        rows.append((-gold, -silver, -bronze, classes[i]))
    rows.sort()  # 튜플은 앞 기준부터 비교하고, 같으면 다음 기준으로 넘어간다
    answer = []
    for row in rows:
        answer.append(row[3])
    return answer
