# 느린 까닭: 딕셔너리 대신 제목 목록과 개수 목록을 두고 index로 제목을 찾는다(찾을 때마다 목록을 앞에서부터 훑는다)
def solution(loans, k):
    titles = []
    counts = []
    shelf = []
    for title in loans:
        if title in titles:
            where = titles.index(title)
            counts[where] += 1
        else:
            titles.append(title)
            counts.append(1)
            where = len(titles) - 1
        if counts[where] == k:
            shelf.append(title)
    return shelf
