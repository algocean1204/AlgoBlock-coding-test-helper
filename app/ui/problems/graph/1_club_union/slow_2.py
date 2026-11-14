# 느린 까닭: 연합을 합칠 때마다 모든 동아리를 훑어 연합 번호를 바꾼다(합칠 때마다 10만 번, 10만 번 합치면 100억 번)
def solution(n, merges):
    label = list(range(n + 1))
    groups = n
    for a, b in merges:
        keep = label[a]
        gone = label[b]
        if keep != gone:
            for club in range(1, n + 1):
                if label[club] == gone:
                    label[club] = keep
            groups -= 1
    return groups
