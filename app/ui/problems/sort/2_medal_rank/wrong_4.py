# 틀린 까닭: 동메달 기준을 빠뜨려, 금·은메달이 같으면 바로 이름으로 가린다
def solution(classes, medals):
    rows = []
    for i in range(len(classes)):
        gold, silver, bronze = medals[i]
        rows.append((-gold, -silver, classes[i]))
    rows.sort()
    return [row[2] for row in rows]
