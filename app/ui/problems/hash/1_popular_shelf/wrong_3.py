# 틀린 까닭: 개수를 올리기 전에 k와 견주어 k + 1번째로 빌려질 때 꽂는다
def solution(loans, k):
    count = {}
    shelf = []
    for title in loans:
        if count.get(title, 0) == k:
            shelf.append(title)
        count[title] = count.get(title, 0) + 1
    return shelf
