# 틀린 까닭: 꽂힌 책을 사전 순으로 정렬해 돌려준다(꽂힌 순서대로여야 한다)
def solution(loans, k):
    count = {}
    shelf = []
    for title in loans:
        count[title] = count.get(title, 0) + 1
        if count[title] == k:
            shelf.append(title)
    return sorted(shelf)
