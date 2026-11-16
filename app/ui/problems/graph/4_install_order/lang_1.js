// 언어 함정: javascript.fill_shared
function solution(n, rules) {
    const after = new Array(n + 1).fill([]); // after[a]: a를 설치해야 설치할 수 있는 패키지들
    const waiting = new Array(n + 1).fill(0); // waiting[b]: b보다 먼저 설치해야 하는데 아직 설치하지 않은 패키지 수(진입 차수)
    for (const [a, b] of rules) {
        after[a].push(b);
        waiting[b] += 1;
    }

    // 자바스크립트에는 힙이 없어 배열로 최소 힙을 직접 만든다(맨 앞이 가장 작은 값)
    const heap = [];
    function push(v) {
        heap.push(v);
        let i = heap.length - 1;
        while (i > 0) {
            const up = (i - 1) >> 1;
            if (heap[up] <= heap[i]) break;
            [heap[up], heap[i]] = [heap[i], heap[up]];
            i = up;
        }
    }
    function pop() {
        const top = heap[0];
        const last = heap.pop();
        if (heap.length > 0) {
            heap[0] = last;
            let i = 0;
            while (true) {
                let small = i;
                const l = 2 * i + 1;
                const r = 2 * i + 2;
                if (l < heap.length && heap[l] < heap[small]) small = l;
                if (r < heap.length && heap[r] < heap[small]) small = r;
                if (small === i) break;
                [heap[small], heap[i]] = [heap[i], heap[small]];
                i = small;
            }
        }
        return top;
    }

    for (let p = 1; p <= n; p++) {
        if (waiting[p] === 0) push(p);
    }
    const order = [];
    while (heap.length > 0) {
        const pkg = pop();
        order.push(pkg);
        for (const nxt of after[pkg]) {
            waiting[nxt] -= 1;
            if (waiting[nxt] === 0) push(nxt);
        }
    }

    if (order.length < n) return []; // 끝내 설치할 수 없는 패키지가 남았다: 규칙에 사이클이 있다
    return order;
}
