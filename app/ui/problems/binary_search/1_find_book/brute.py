def solution(books, queries):
    answer = []
    for target in queries:
        position = -1
        for i in range(len(books)):
            if books[i] == target:
                position = i
        answer.append(position)
    return answer
