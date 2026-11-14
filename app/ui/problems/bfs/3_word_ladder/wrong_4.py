# 틀린 까닭: 이웃 가운데 goal과 같은 자리의 글자가 가장 많은 낱말로만 욕심내어 옮겨 간다(멀어졌다 돌아와야 하는 길을 놓친다)
def solution(start, goal, dictionary):
    if goal not in dictionary:
        return -1

    def same(a, b):
        return sum(1 for x, y in zip(a, b) if x == y)

    word, count, used = start, 0, {start}
    while word != goal:
        best = None
        for other in dictionary:
            if other not in used and same(word, other) == len(word) - 1:
                if best is None or same(other, goal) > same(best, goal):
                    best = other
        if best is None:
            return -1
        used.add(best)
        word, count = best, count + 1
    return count
