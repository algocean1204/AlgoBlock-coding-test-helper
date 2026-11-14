def solution(records, k):
    board = []  # (시간, 들어온 순서): 이 순서대로 정렬하면 기록판의 순위다
    alerts = 0
    for order, record in enumerate(records):
        minutes, seconds = record.split(":")
        entry = (int(minutes) * 60 + int(seconds), order)
        board.append(entry)
        rank = sorted(board).index(entry) + 1
        if rank <= k:
            alerts += 1
    return alerts
