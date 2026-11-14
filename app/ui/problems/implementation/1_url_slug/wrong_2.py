# 틀린 까닭: 규칙 3의 낱말을 언제나 모두 빼서, 그 낱말만 있는 제목에서 목록이 비어 버린다
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
    words = [word for word in clean(title) if word not in SKIP]
    if not words:
        return unique("", taken)
    slug = words[0][:24]
    for word in words[1:]:
        if len(slug) + 1 + len(word) > 24:
            break
        slug += "-" + word
    return unique(slug, taken)
