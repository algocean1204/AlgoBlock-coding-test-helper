def solution(apples, pears, low, high):
    # 상자 크기마다 (남는 수, 크기, 상자 수)를 모두 적어 두고, 남는 수가 가장 적고 크기가 가장 큰 것을 고른다
    table = []
    for size in range(low, high + 1):
        apple_boxes = apples // size
        pear_boxes = pears // size
        left = (apples - apple_boxes * size) + (pears - pear_boxes * size)
        table.append((left, size, apple_boxes + pear_boxes))
    fewest = min(row[0] for row in table)
    best = max(row for row in table if row[0] == fewest)
    return [best[1], best[2]]
