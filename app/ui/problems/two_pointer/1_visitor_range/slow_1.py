# 느린 까닭: 질문마다 start일부터 end일까지 다시 더한다(질문 5만 개 × 날 10만 개)
def solution(visitors, queries):
    answer = []
    for start, end in queries:
        total = 0
        for i in range(start - 1, end):
            total += visitors[i]
        answer.append(total)
    return answer
