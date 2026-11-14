# 틀린 까닭: '이상'을 '초과'로 읽어 전체 용량이 limit과 같은 폴더를 빠뜨린다
def solution(parent, files, limit):
    n = len(parent)
    children = [[] for _ in range(n)]
    for folder in range(n):
        if parent[folder] != -1:
            children[parent[folder]].append(folder)
    order = []
    stack = [0]
    while stack:
        folder = stack.pop()
        order.append(folder)
        for child in children[folder]:
            stack.append(child)
    total = list(files)
    for folder in reversed(order):
        if parent[folder] != -1:
            total[parent[folder]] += total[folder]
    return sum(1 for size in total if size > limit)
