# 틀린 까닭: 소문자로 바꾸고 다른 글자를 지우기 전에 규칙 3의 낱말인지 견주어 "The"나 "of,"를 빼지 못한다
SKIP = ["a", "an", "the", "of", "and"]


def clean(title):
    words = []
    for word in title.split():
        kept = "".join(ch for ch in word.lower() if ch in "abcdefghijklmnopqrstuvwxyz0123456789")
        if kept:
            words.append(kept)
    return words


def unique(slug, taken):
    number = 2
    result = slug
    while result in taken:
        result = slug + "-" + str(number)
        number += 1
    return result


def solution(title, taken):
    raw = title.split()
    left = [word for word in raw if word not in SKIP]
    if left:
        raw = left
    words = clean(" ".join(raw))
    slug = words[0][:24]
    for word in words[1:]:
        if len(slug) + 1 + len(word) > 24:
            break
        slug += "-" + word
    return unique(slug, taken)
