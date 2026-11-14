# 틀린 까닭: 재귀로 안쪽 폴더의 용량을 구하면서 재귀 깊이 제한을 늘리지 않는다(폴더가 아주 여러 겹이면 실행 오류가 난다)
def solution(parent, files, limit):
    n = len(parent)
    children = [[] for _ in range(n)]
    for folder in range(n):
        if parent[folder] != -1:
            children[parent[folder]].append(folder)
    total = [0] * n

    def size_of(folder):
        total[folder] = files[folder]
        for child in children[folder]:
            total[folder] += size_of(child)
        return total[folder]

    size_of(0)
    return sum(1 for size in total if size >= limit)
