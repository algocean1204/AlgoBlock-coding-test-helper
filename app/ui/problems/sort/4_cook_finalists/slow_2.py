# 느린 까닭: 맛 점수 순으로 정렬은 했지만, 참가자마다 앞에 지나간 사람을 모두 다시 확인한다(최댓값 하나만 들고 다니면 된다)
def solution(taste, look):
    people = sorted(zip(taste, look), key=lambda person: -person[0])
    count = 0
    for i in range(len(people)):
        my_taste, my_look = people[i]
        beaten = False
        for j in range(i):
            if people[j][0] > my_taste and people[j][1] > my_look:
                beaten = True
                break
        if not beaten:
            count += 1
    return count
