def solution(visitors, queries):
    # prefix[i]: 1일부터 i일까지 방문자 수의 합. prefix[0]은 아무 날도 더하지 않은 0
    prefix = [0] * (len(visitors) + 1)
    for i in range(len(visitors)):
        prefix[i + 1] = prefix[i] + visitors[i]
    answer = []
    for start, end in queries:
        answer.append(prefix[end] - prefix[start - 1])
    return answer
