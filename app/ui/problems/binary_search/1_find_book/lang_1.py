# 언어 함정: python.true_division
def solution(books, queries):
    answer = []
    for target in queries:
        left = 0
        right = len(books) - 1
        position = -1
        while left <= right:
            mid = (left + right) / 2
            if books[mid] == target:
                position = mid
                break
            elif books[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        answer.append(position)
    return answer
