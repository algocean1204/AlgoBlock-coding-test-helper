# 틀린 까닭: 개수가 k 이상일 때마다 담아 같은 책을 여러 번 담는다
def solution(loans, k):
    count = {}
    shelf = []
    for title in loans:
        count[title] = count.get(title, 0) + 1
        if count[title] >= k:
            shelf.append(title)
    return shelf
