def solution(tiles, m):
    # 순열 도구 없이 재귀로 타일을 한 장씩 붙여 가며 글자 그대로의 배치를 모두 만든다
    n = len(tiles)
    used = [False] * n
    made = {}

    def build(text):
        if len(text) >= 2 and text[0] != "0":
            made[text] = True  # 맨 앞이 0이 아니면 글자가 다른 배치는 값도 다르다
        for i in range(n):
            if not used[i]:
                used[i] = True
                build(text + tiles[i])
                used[i] = False

    build("")
    return sum(1 for text in made if int(text) % m == 0)
