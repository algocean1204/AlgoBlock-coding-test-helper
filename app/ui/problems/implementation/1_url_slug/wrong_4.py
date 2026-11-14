# 틀린 까닭: "-2"를 한 번만 붙이고, 그 글도 taken에 있는지 다시 확인하지 않는다
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
        if len(slug) + 1 + len(word) > 24:
            break
        slug += "-" + word
    if slug in taken:
        slug += "-2"
    return slug
