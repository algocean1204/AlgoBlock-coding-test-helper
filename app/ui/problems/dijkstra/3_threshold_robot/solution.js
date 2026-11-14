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

function solution(ground) {
    const rows = ground.length;
    const cols = ground[0].length;
    // 그 칸까지 가는 길에서 넘는 가장 높은 턱의 최솟값
    const highest = Array.from({ length: rows }, () => new Array(cols).fill(Infinity));
    highest[0][0] = 0;
    const heap = new MinHeap();
    heap.push([0, 0, 0]);
    while (heap.size() > 0) {
        const [h, r, c] = heap.pop();
        if (h > highest[r][c]) continue;
        if (r === rows - 1 && c === cols - 1) return h;
        for (const [nr, nc] of [[r - 1, c], [r + 1, c], [r, c - 1], [r, c + 1]]) {
            if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) {
                const ledge = Math.abs(ground[nr][nc] - ground[r][c]);
                const cur = Math.max(h, ledge); // 합이 아니라 가장 높은 턱
                if (cur < highest[nr][nc]) {
                    highest[nr][nc] = cur;
                    heap.push([cur, nr, nc]);
                }
            }
        }
    }
    return highest[rows - 1][cols - 1];
}
