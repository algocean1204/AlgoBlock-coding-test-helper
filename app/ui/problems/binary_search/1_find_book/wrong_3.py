# 틀린 까닭: 들어갈 자리를 구한 뒤 그 자리가 배열 끝(길이와 같은 자리)인지 확인하지 않고 값을 읽어, 모든 번호보다 큰 번호를 찾으면 오류가 난다
def solution(books, queries):
    answer = []
    for target in queries:
        left = 0
        right = len(books)
        while left < right:
            mid = (left + right) // 2
            if books[mid] < target:
                left = mid + 1
            else:
                right = mid
        if books[left] == target:
            answer.append(left)
        else:
            answer.append(-1)
    return answer
