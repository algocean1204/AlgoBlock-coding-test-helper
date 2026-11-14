# 틀린 까닭: reverse=True로 모든 기준을 한꺼번에 뒤집어, 메달이 같을 때 이름까지 사전 역순이 된다
def solution(classes, medals):
    rows = []
    for i in range(len(classes)):
        gold, silver, bronze = medals[i]
        rows.append((gold, silver, bronze, classes[i]))
    rows.sort(reverse=True)
    return [row[3] for row in rows]
