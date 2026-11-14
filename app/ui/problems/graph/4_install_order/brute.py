def solution(n, rules):
    installed = set()
    order = []
    while len(order) < n:
        chosen = None
        for package in range(1, n + 1):
            if package in installed:
                continue
            if all(a in installed for a, b in rules if b == package):
                chosen = package
                break
        if chosen is None:
            return []
        installed.add(chosen)
        order.append(chosen)
    return order
