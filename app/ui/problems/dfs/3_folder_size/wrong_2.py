# 틀린 까닭: 번호가 큰 폴더부터 차례로 부모에 더한다(바깥 폴더의 번호가 언제나 더 작다고 잘못 가정한다)
def solution(parent, files, limit):
    n = len(parent)
    total = list(files)
    for folder in range(n - 1, 0, -1):
        total[parent[folder]] += total[folder]
    return sum(1 for size in total if size >= limit)
