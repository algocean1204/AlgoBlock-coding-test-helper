def solution(visitors, queries):
    answer = []
    for start, end in queries:
        total = 0
        for day in range(start, end + 1):
            total += visitors[day - 1]
        answer.append(total)
    return answer
