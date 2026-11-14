SKIP = ["a", "an", "the", "of", "and"]
LIMIT = 24


def solution(title, taken):
    # 1. 빈칸으로 나누기: split()은 이어진 빈칸과 양 끝 빈칸에서 빈 낱말을 만들지 않는다
    words = title.split()

    # 2. 낱말마다 소문자로 바꾸고 영문 소문자·숫자만 남기기. 다 지워진 낱말은 뺀다
    cleaned = []
    for word in words:
        kept = ""
        for ch in word.lower():
            if ch in "abcdefghijklmnopqrstuvwxyz0123456789":
                kept += ch
        if kept != "":
            cleaned.append(kept)
    words = cleaned

    # 3. 규칙 3의 낱말 빼기. 다 빠져 목록이 비면 빼지 않는다
    left = []
    for word in words:
        if word not in SKIP:
            left.append(word)
    if len(left) > 0:
        words = left

    # 4. 낱말 단위로 이어 붙이다가 길이가 24를 넘게 되면 멈춘다
    slug = words[0][:LIMIT]
    for word in words[1:]:
        if len(slug) + 1 + len(word) > LIMIT:
            break
        slug = slug + "-" + word

    # 5. taken에 있으면 -2, -3, … 을 붙여 본다
    taken = set(taken)
    if slug not in taken:
        return slug
    number = 2
    while slug + "-" + str(number) in taken:
        number += 1
    return slug + "-" + str(number)
