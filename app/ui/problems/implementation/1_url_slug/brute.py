import re


def solution(title, taken):
    # 정규식으로 낱말을 뽑고 다듬는다(solution.py는 글자를 하나씩 본다)
    words = [re.sub("[^a-z0-9]", "", word.lower()) for word in re.split(" +", title)]
    words = [word for word in words if word]
    left = [word for word in words if word not in ("a", "an", "the", "of", "and")]
    if left:
        words = left

    # 앞에서 j개 낱말을 이은 글 가운데 길이 24 이하인 것의 가장 큰 j를 고른다(없으면 첫 낱말의 앞 24글자)
    slug = words[0][:24]
    for j in range(len(words), 0, -1):
        joined = "-".join(words[:j])
        if len(joined) <= 24:
            slug = joined
            break

    # 붙일 수 있는 이름을 차례로 늘어놓고 taken에 없는 첫 이름을 고른다
    candidates = [slug] + [f"{slug}-{number}" for number in range(2, len(taken) + 3)]
    for candidate in candidates:
        if candidate not in taken:
            return candidate
