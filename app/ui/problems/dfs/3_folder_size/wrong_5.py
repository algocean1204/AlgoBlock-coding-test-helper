# 틀린 까닭: 방문 순서를 거꾸로 하지 않고 바깥에서 안쪽 순서 그대로 부모에 더한다(안쪽 폴더의 합이 다 정해지기 전에 올려 보낸다)
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
    for folder in order:
        if parent[folder] != -1:
            total[parent[folder]] += total[folder]
    return sum(1 for size in total if size >= limit)
