# 언어 함정: python.negative_index @ "parent[0]은 -1입니다"
# 재귀로 쓰면: size_of(folder) = files[folder] + (안쪽 폴더마다 size_of(child)의 합).
# 폴더가 10만 겹으로 들어 있을 수 있어 재귀가 10만 번 깊어진다. 그래서 재귀 대신,
# 바깥에서 안쪽으로 방문한 순서를 스택으로 구하고 그 순서를 거꾸로 따라가며 더한다(안쪽이 먼저 끝난다).
def solution(parent, files, limit):
    n = len(parent)
    children = [[] for _ in range(n)]
    for folder in range(n):
        if parent[folder] != -1:
            children[parent[folder]].append(folder)
    # 0번에서 출발해 바깥에서 안쪽으로 방문한 순서를 적는다(재귀 대신 스택)
    order = []
    stack = [0]
    while stack:
        folder = stack.pop()
        order.append(folder)
        for child in children[folder]:
            stack.append(child)
    # 이 순서를 거꾸로 보면 안쪽 폴더가 언제나 바깥 폴더보다 먼저 나온다.
    # 안쪽 폴더의 전체 용량이 다 정해진 뒤에 바깥 폴더에 더해 올린다.
    total = list(files)
    for folder in reversed(order):
        total[parent[folder]] += total[folder]
    count = 0
    for size in total:
        if size >= limit:
            count += 1
    return count
