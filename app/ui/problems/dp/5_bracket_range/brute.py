def solution(values, signs):
    # 괄호를 치는 모든 방법을 재귀로 만들어 보고, 나올 수 있는 값을 모두 모아 가장 큰 것과 가장 작은 것을 고른다
    def calc(a, sign, b):
        if sign == '+':
            return a + b
        if sign == '-':
            return a - b
        return a if a >= b else b

    def results(i, j):
        if i == j:
            return {values[i]}
        out = set()
        for k in range(i, j):  # signs[k]를 맨 마지막에 계산하는 경우
            for left in results(i, k):
                for right in results(k + 1, j):
                    out.add(calc(left, signs[k], right))
        return out

    every = results(0, len(values) - 1)
    return [max(every), min(every)]
