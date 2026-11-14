# 느린 까닭: 찾을 때마다 in과 index로 books를 앞에서부터 훑는다(찾기 10만 번 × 책 10만 권)
def solution(books, queries):
    answer = []
    for target in queries:
        if target in books:
            answer.append(books.index(target))
        else:
            answer.append(-1)
    return answer
