# 틀린 까닭: prefix[end] - prefix[start]로 계산해 start일의 방문자 수까지 빼 버린다
def solution(visitors, queries):
    prefix = [0] * (len(visitors) + 1)
    for i in range(len(visitors)):
        prefix[i + 1] = prefix[i] + visitors[i]
    answer = []
    for start, end in queries:
        answer.append(prefix[end] - prefix[start])
    return answer
