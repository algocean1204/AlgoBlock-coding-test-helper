# 틀린 까닭: 하루씩 건너뛰며 짝수 번째 날의 합과 홀수 번째 날의 합 가운데 큰 쪽을 고른다(이틀 연달아 쉬는 편이 나을 때를 놓친다)
def solution(pay):
    even = sum(pay[0::2])
    odd = sum(pay[1::2])
    return max(even, odd)
