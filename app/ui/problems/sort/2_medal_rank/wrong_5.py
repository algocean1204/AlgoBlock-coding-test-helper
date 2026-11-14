# 틀린 까닭: 메달 셋을 100씩 곱해 점수 하나로 합친다(값이 100까지라 은메달 100개가 금메달 1개와 같아진다)
def solution(classes, medals):
    rows = []
    for i in range(len(classes)):
        gold, silver, bronze = medals[i]
        rows.append((-(gold * 10000 + silver * 100 + bronze), classes[i]))
    rows.sort()
    return [row[1] for row in rows]
