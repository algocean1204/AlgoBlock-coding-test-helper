# 틀린 까닭: 정렬한 뒤 바로 앞 사람과만 비교한다(더 앞의 사람이 나를 떨어뜨릴 수 있다)
def solution(taste, look):
    people = sorted(zip(taste, look), key=lambda person: (-person[0], person[1]))
    count = 0
    for i in range(len(people)):
        if i > 0 and people[i - 1][0] > people[i][0] and people[i - 1][1] > people[i][1]:
            continue
        count += 1
    return count
