# 느린 까닭: 폴더마다 바깥 폴더로 한 겹씩 올라가며 자기 파일 용량을 더한다(10만 겹이면 약 50억 번)
def solution(parent, files, limit):
    n = len(parent)
    total = [0] * n
    for folder in range(n):
        outer = folder
        while outer != -1:
            total[outer] += files[folder]
            outer = parent[outer]
    return sum(1 for size in total if size >= limit)
