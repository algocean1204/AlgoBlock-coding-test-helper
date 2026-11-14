# 틀린 까닭: 메달 총합이 많은 순으로 세우고, 총합이 같으면 이름 순으로 세운다(금메달을 먼저 봐야 한다)
def solution(classes, medals):
    rows = []
    for i in range(len(classes)):
        rows.append((-sum(medals[i]), classes[i]))
    rows.sort()
    return [row[1] for row in rows]
