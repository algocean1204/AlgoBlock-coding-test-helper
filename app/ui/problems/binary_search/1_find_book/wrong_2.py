# 틀린 까닭: 찾는 번호가 없을 때 -1 대신 반복이 멈춘 자리(그 번호가 들어갈 자리)를 돌려준다
def solution(books, queries):
    answer = []
    for target in queries:
        left = 0
        right = len(books) - 1
        while left <= right:
            mid = (left + right) // 2
            if books[mid] == target:
                left = mid
                break
            elif books[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        answer.append(left)
    return answer
