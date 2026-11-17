// 언어 함정: javascript.string_plus @ "공백 하나씩으로 구분한 문자열"
// 자바스크립트에는 우선순위 큐가 없어서 배열로 최소 힙을 직접 만든다.
// 항목은 [시간, ...]이고 첫 칸(시간)이 작은 것이 위로 올라온다.
class MinHeap {
    constructor() {
        this.a = [];
    }
    size() {
        return this.a.length;
    }
    push(item) {
        const a = this.a;
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
        const a = this.a;
        const top = a[0];
        const last = a.pop();
        if (a.length > 0) {
            a[0] = last;
            let i = 0;
            while (true) {
                let s = i;
                const l = 2 * i + 1, r = 2 * i + 2;
                if (l < a.length && a[l][0] < a[s][0]) s = l;
                if (r < a.length && a[r][0] < a[s][0]) s = r;
                if (s === i) break;
                [a[s], a[i]] = [a[i], a[s]];
                i = s;
            }
        }
        return top;
    }
}

function solution(routes, start, goal) {
    // 선착장 이름마다 0부터 번호를 매기고, 번호로 인접 목록을 만든다
    const id = new Map();
    const graph = [];
    for (const route of routes) {
        const [departure, arrival, minutes] = route.split(" ");
        for (const name of [departure, arrival]) {
            if (!id.has(name)) {
                id.set(name, id.size);
                graph.push([]);
            }
        }
        graph[id.get(departure)].push([id.get(arrival), minutes]);
    }

    const source = id.get(start);
    const target = id.get(goal);
    const dist = new Array(id.size).fill(Infinity);
    dist[source] = 0;
    const heap = new MinHeap();
    heap.push([0, source]);
    while (heap.size() > 0) {
        const [d, now] = heap.pop();
        if (d > dist[now]) continue; // 이미 더 빠른 시간으로 확정된 선착장
        if (now === target) return d; // 도착점은 큐에서 꺼낼 때 확정된다
        for (const [nxt, minutes] of graph[now]) {
            if (d + minutes < dist[nxt]) {
                dist[nxt] = d + minutes;
                heap.push([dist[nxt], nxt]);
            }
        }
    }
    return -1;
}
