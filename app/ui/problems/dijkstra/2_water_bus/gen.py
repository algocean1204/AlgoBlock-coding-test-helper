LARGE = 2

POOL = ["pier", "mill", "tower", "cave", "isle", "port", "bay", "reef", "dock", "lake", "hill", "cove", "inn", "farm", "gate", "well"]


def valid(routes, start, goal):
    if not 1 <= len(routes) <= 60_000 or start == goal:
        return False
    names = set()
    for route in routes:
        parts = route.split(" ")
        if len(parts) != 3:
            return False
        departure, arrival, minutes = parts
        for name in (departure, arrival):
            if not (1 <= len(name) <= 10 and all("a" <= ch <= "z" for ch in name)):
                return False
        if departure == arrival or not (minutes.isdigit() and minutes[0] != "0" and 1 <= int(minutes) <= 1000):
            return False
        names.add(departure)
        names.add(arrival)
    return start in names and goal in names


def unique_names(rng, count, shortest=3, longest=10):
    seen = set()
    names = []
    while len(names) < count:
        name = rng.word(rng.randint(shortest, longest))
        if name not in seen:
            seen.add(name)
            names.append(name)
    return names


def random_routes(rng, names, count, high):
    routes = []
    while len(routes) < count:
        a, b = rng.choice(names), rng.choice(names)
        if a != b:
            routes.append(f"{a} {b} {rng.randint(1, high)}")
    return routes


def with_ends(rng, routes):
    """routes에 나오는 선착장 가운데 서로 다른 둘을 start, goal로 고른다."""
    names = sorted({name for route in routes for name in route.split()[:2]})
    start, goal = rng.sample(names, 2)
    return [routes, start, goal]


def small(rng):
    cases = [
        [["a b 1"], "a", "b"],
        [["a b 1"], "b", "a"],  # 거꾸로는 못 간다
        [["ab ba 1000", "ba ab 1"], "ab", "ba"],
        [["x y 9", "x y 2", "x y 5"], "x", "y"],  # 같은 두 선착장 사이 노선 셋
        [["a aa 1", "aa aaa 1", "a aaa 3"], "a", "aaa"],
        [["home mall 1", "mall home 1", "gate home 1"], "home", "gate"],  # goal에서 나가는 노선만 있다
        [["mall home 1", "mall gate 1"], "home", "gate"],  # start로 들어오는 노선만 있다
        [["s a 1", "s g 50", "a b 1", "b c 1", "c g 1", "g s 1"], "s", "g"],  # 먼저 큐에 들어간 도착점보다 돌아가는 길이 빠르다
        [["p q 5", "q r 5", "r p 1", "p r 100"], "p", "r"],
        [["a b 2", "b d 2", "a c 1", "c d 3"], "a", "d"],  # 두 길의 시간이 같다
        [["abcdefghij klmnopqrst 1000", "klmnopqrst z 1000", "abcdefghij z 1000", "z abcdefghij 1"], "abcdefghij", "z"],
        [["a b 9", "a b 10", "b c 1"], "a", "c"],  # 시간을 글자로 비교하면 "10"이 "9"보다 작다
        [["ab c 1", "a bc 5", "bc ab 1"], "a", "bc"],  # 두 이름을 이어 붙이면 "ab"+"c"와 "a"+"bc"가 같아진다
    ]
    for count, size, high in ((10, 6, 9), (16, 8, 20), (25, 12, 1000), (40, 16, 9)):
        cases.append(with_ends(rng, random_routes(rng, rng.sample(POOL, size), count, high)))
    for count, size, high in ((50, 20, 100), (60, 30, 1000)):
        cases.append(with_ends(rng, random_routes(rng, unique_names(rng, size, 1, 5), count, high)))
    return cases


def random_small(rng):
    routes = random_routes(rng, rng.sample(POOL[:8], rng.randint(2, 5)), rng.randint(1, 8), 9)
    return with_ends(rng, routes)


def large(rng, index):
    if index == 0:  # start에서 5만 9천 곳에 닿지만 goal로 들어오는 노선이 없다: 닿는 곳을 모두 본 뒤에야 -1을 안다
        names = unique_names(rng, 59_001)
        start, goal, order = names[0], names[1], [names[0]] + names[2:]
        routes = [f"{order[rng.randint(0, i - 1)]} {order[i]} {rng.randint(1, 1000)}" for i in range(1, len(order))]
        routes.append(f"{goal} {rng.choice(order)} {rng.randint(1, 1000)}")
        while len(routes) < 60_000:
            a, b = rng.choice(order), rng.choice(order)
            if a != b:
                routes.append(f"{a} {b} {rng.randint(1, 1000)}")
        return [rng.shuffle(routes), start, goal]
    # 선착장 6만 곳이 한 줄로 이어지고 goal이 맨 끝에 있다: goal이 가장 늦게 확정된다
    order = unique_names(rng, 60_000)
    last = len(order) - 1
    routes = [f"{order[i]} {order[i + 1]} {rng.randint(1, 1000)}" for i in range(last)]
    while len(routes) < 60_000:
        i = rng.randint(0, last - 1)
        if rng.chance(1, 2):  # 같은 두 선착장 사이의 다른 노선
            routes.append(f"{order[i]} {order[i + 1]} {rng.randint(1, 1000)}")
        else:  # 뒤로 돌아가는 노선(한 방향이라 지름길이 되지 않는다)
            routes.append(f"{order[rng.randint(i + 1, last)]} {order[i]} {rng.randint(1, 1000)}")
    return [rng.shuffle(routes), order[0], order[last]]
