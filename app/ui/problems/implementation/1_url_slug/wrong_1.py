# 틀린 까닭: 낱말을 모두 이어 붙인 뒤 앞 24글자로 잘라, 낱말 가운데가 잘리거나 빼기로 끝난다
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
    words = clean(title)
    left = [word for word in words if word not in SKIP]
    if left:
        words = left
    slug = "-".join(words)[:24]
    return unique(slug, taken)
