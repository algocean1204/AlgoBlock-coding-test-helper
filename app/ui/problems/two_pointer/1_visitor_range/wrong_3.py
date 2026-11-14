# 틀린 까닭: 맨 앞에 0을 두지 않은 누적 합을 써서, start가 1일 때 prefix[-1](전체 합)을 빼 버린다
def solution(visitors, queries):
    prefix = []  # prefix[i]: 1일부터 i + 1일까지의 합
    total = 0
    for count in visitors:
        total += count
        prefix.append(total)
    answer = []
    for start, end in queries:
        answer.append(prefix[end - 1] - prefix[start - 2])
    return answer
