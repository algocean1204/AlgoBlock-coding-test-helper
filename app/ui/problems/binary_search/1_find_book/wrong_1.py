# 틀린 까닭: 오른쪽 끝을 마지막 자리(길이 - 1)로 두고도 left < right 동안만 돌아, 마지막에 남은 한 자리를 확인하지 않는다
def solution(books, queries):
    answer = []
    for target in queries:
        left = 0
        right = len(books) - 1
        position = -1
        while left < right:
            mid = (left + right) // 2
            if books[mid] == target:
                position = mid
                break
            elif books[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        answer.append(position)
    return answer
