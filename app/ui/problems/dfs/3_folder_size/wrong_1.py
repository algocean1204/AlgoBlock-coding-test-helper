# 틀린 까닭: 바로 안쪽 폴더의 파일까지만 더한다(그보다 더 안쪽 폴더의 파일을 빠뜨린다)
def solution(parent, files, limit):
    n = len(parent)
    total = list(files)
    for folder in range(n):
        if parent[folder] != -1:
            total[parent[folder]] += files[folder]
    return sum(1 for size in total if size >= limit)
