# 틀린 까닭: 이으면 길이가 꼭 24가 되는 낱말도 붙이지 않는다('넘으면'을 '이상이면'으로 옮김)
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
    slug = words[0][:24]
    for word in words[1:]:
        if len(slug) + 1 + len(word) >= 24:
            break
        slug += "-" + word
    return unique(slug, taken)
