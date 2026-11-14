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

function solution(n, roads) {
    const graph = Array.from({ length: n + 1 }, () => []);
    for (const [a, b, time] of roads) {
        graph[a].push([b, time]);
        graph[b].push([a, time]);
    }

    const dist = new Array(n + 1).fill(Infinity);
    dist[1] = 0;
    const heap = new MinHeap();
    heap.push([0, 1]);
    while (heap.size() > 0) {
        const [d, now] = heap.pop();
        if (d > dist[now]) continue; // 이미 더 짧은 시간으로 확정된 마을
        for (const [nxt, time] of graph[now]) {
            if (d + time < dist[nxt]) {
                dist[nxt] = d + time;
                heap.push([dist[nxt], nxt]);
            }
        }
    }
    return dist.slice(1);
}
