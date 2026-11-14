# 느린 까닭: 질문마다 잘라 낸 구간을 sum으로 더한다(sum이 빨라도 질문 5만 개 × 날 10만 개를 모두 본다)
def solution(visitors, queries):
    return [sum(visitors[start - 1:end]) for start, end in queries]
