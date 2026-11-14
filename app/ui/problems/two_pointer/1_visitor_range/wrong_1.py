# 틀린 까닭: prefix[end - 1] - prefix[start - 1]로 계산해 end일의 방문자 수를 빠뜨린다
def solution(visitors, queries):
    prefix = [0] * (len(visitors) + 1)
    for i in range(len(visitors)):
        prefix[i + 1] = prefix[i] + visitors[i]
    answer = []
    for start, end in queries:
        answer.append(prefix[end - 1] - prefix[start - 1])
    return answer
