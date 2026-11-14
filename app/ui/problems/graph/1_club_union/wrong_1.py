# 틀린 까닭: 기록 하나마다 연합이 하나씩 준다고 본다(이미 같은 연합인 기록은 연합 수를 줄이지 않는다)
def solution(n, merges):
    return max(1, n - len(merges))
