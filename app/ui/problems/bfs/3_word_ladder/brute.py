def solution(start, goal, dictionary):
    # 큐를 쓰지 않는다: 두 낱말이 한 자리만 다르면 '앞 낱말의 횟수 + 1'로 줄이는 일을 더 바뀌지 않을 때까지 되풀이한다
    def one_apart(a, b):
        return sum(1 for i in range(len(a)) if a[i] != b[i]) == 1

    big = len(dictionary) + 1
    count = {word: big for word in dictionary}
    count[start] = 0
    changed = True
    while changed:
        changed = False
        for a in list(count):
            for b in dictionary:
                if count[a] + 1 < count[b] and one_apart(a, b):
                    count[b] = count[a] + 1
                    changed = True
    if goal not in dictionary or count[goal] == big:
        return -1
    return count[goal]
