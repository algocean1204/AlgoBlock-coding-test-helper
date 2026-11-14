// 가장 작은 값을 꺼내는 힙(배열로 만든 이진 힙)
class MinHeap {
    constructor() { this.items = []; }
    get size() { return this.items.length; }
    push(item) {
        const a = this.items;
        a.push(item);
        let i = a.length - 1;
        while (i > 0) {
            const p = (i - 1) >> 1;
            if (a[p][0] <= a[i][0]) break;
            [a[p], a[i]] = [a[i], a[p]];
            i = p;
        }
    }
    pop() {
        const a = this.items;
        const top = a[0];
        const last = a.pop();
        if (a.length > 0) {
            a[0] = last;
            let i = 0;
            while (true) {
                const l = 2 * i + 1, r = l + 1;
                let m = i;
                if (l < a.length && a[l][0] < a[m][0]) m = l;
                if (r < a.length && a[r][0] < a[m][0]) m = r;
                if (m === i) break;
                [a[m], a[i]] = [a[i], a[m]];
                i = m;
            }
        }
        return top;
    }
}

function dijkstra(graph, n, start) {
    const dist = new Array(n + 1).fill(Infinity);
    dist[start] = 0;
    const heap = new MinHeap();
    heap.push([0, start]);
    while (heap.size > 0) {
        const [d, now] = heap.pop();
        if (d > dist[now]) continue;
        for (const [nxt, time] of graph[now]) {
            if (d + time < dist[nxt]) {
                dist[nxt] = d + time;
                heap.push([dist[nxt], nxt]);
            }
        }
    }
    return dist;
}

function solution(n, roads, farms, market) {
    const small = Array.from({ length: n + 1 }, () => []);  // 작은 트럭: u → v, slow분
    const bigBack = Array.from({ length: n + 1 }, () => []);  // 큰 트럭의 도로를 거꾸로 뒤집은 것: v → u, fast분
    for (const [u, v, slow, fast] of roads) {
        small[u].push([v, slow]);
        bigBack[v].push([u, fast]);
    }

    // 뒤집은 그래프에서 시장으로부터의 거리 = 각 마을에서 시장까지 큰 트럭이 걸리는 시간
    const toMarket = dijkstra(bigBack, n, market);

    const gather = new Array(n + 1).fill(0);  // gather[m]: 작은 트럭이 모두 m번 마을에 모이는 시각(가장 늦게 도착한 트럭)
    for (const farm of farms) {
        const arrive = dijkstra(small, n, farm);
        for (let m = 1; m <= n; m++) {
            gather[m] = Math.max(gather[m], arrive[m]);
        }
    }

    let answer = Infinity;
    for (let m = 1; m <= n; m++) {  // 모이는 마을을 모두 해 본다. 닿지 못하는 곳은 무한대라 뽑히지 않는다
        answer = Math.min(answer, gather[m] + toMarket[m]);
    }
    return answer === Infinity ? -1 : answer;
}
