import json
import sys


def solution(numbers):
    return sum(numbers)


if __name__ == "__main__":
    print(json.dumps(solution(*json.load(sys.stdin)), ensure_ascii=False))
