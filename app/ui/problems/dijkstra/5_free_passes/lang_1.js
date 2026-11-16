// 언어 함정: javascript.fill_shared
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

function solution(n, roads, k) {
    const graph = new Array(n + 1).fill([]);
    for (const [u, v, toll] of roads) {
        graph[u].push([v, toll]);
        graph[v].push([u, toll]);
    }

    // dist[city][used][just]: 통행권을 used장 쓰고 city에 왔을 때 낸 통행료 합의 최솟값
    // just는 바로 앞 도로에 통행권을 썼으면 1, 통행료를 냈으면(또는 아직 출발 전이면) 0
    const dist = Array.from({ length: n + 1 }, () => Array.from({ length: k + 1 }, () => [Infinity, Infinity]));
    dist[1][0][0] = 0;
    const heap = new MinHeap();
    heap.push([0, 1, 0, 0]);
    while (heap.size() > 0) {
        const [cost, city, used, just] = heap.pop();
        if (cost > dist[city][used][just]) continue;
        if (city === n) return cost; // 몇 장을 썼든 n번 도시를 처음 꺼낸 값이 가장 싸다(통행권은 남겨도 된다)
        for (const [nxt, toll] of graph[city]) {
            if (cost + toll < dist[nxt][used][0]) { // 통행료를 낸다
                dist[nxt][used][0] = cost + toll;
                heap.push([cost + toll, nxt, used, 0]);
            }
            if (used < k && just === 0 && cost < dist[nxt][used + 1][1]) { // 통행권을 쓴다(바로 앞 도로에 쓰지 않았을 때만)
                dist[nxt][used + 1][1] = cost;
                heap.push([cost, nxt, used + 1, 1]);
            }
        }
    }
    return -1;
}
