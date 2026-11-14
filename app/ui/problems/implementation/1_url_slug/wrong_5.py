# 틀린 까닭: 길이를 넘는 낱말만 건너뛰고 그 뒤의 짧은 낱말은 계속 붙인다(멈춰야 한다)
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
            continue
        slug += "-" + word
    return unique(slug, taken)
