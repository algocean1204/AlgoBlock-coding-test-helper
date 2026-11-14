# 틀린 까닭: DFS로 사전 순서대로 따라가다 처음 goal에 닿은 횟수를 답으로 한다(처음 찾은 길이 가장 짧다는 보장이 없다)
import sys

sys.setrecursionlimit(100_000)


def solution(start, goal, dictionary):
    if goal not in dictionary:
        return -1
    visited = {start}

    def one_apart(a, b):
        return sum(1 for x, y in zip(a, b) if x != y) == 1

    def dfs(word, count):
        if word == goal:
            return count
        for other in dictionary:
            if other not in visited and one_apart(word, other):
                visited.add(other)
                found = dfs(other, count + 1)
                if found != -1:
                    return found
        return -1

    return dfs(start, 0)
