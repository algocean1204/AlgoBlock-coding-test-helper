function solution(pickup, minutes, booked) {
    const must = new Array(pickup.length).fill(false);  // 꼭 받아야 하는 주문인가
    for (const b of booked) must[b] = true;
    const order = pickup.map((_, i) => i).sort((a, b) => pickup[a] - pickup[b]);  // 찾으러 오는 시각이 이른 주문부터
    // JavaScript에는 힙이 없어 배열로 최대 힙을 직접 만든다 (부모가 자식보다 크거나 같다)
    const heap = [];  // 되무를 수 있는 받은 주문의 만드는 시간
    function push(value) {
        heap.push(value);
        let i = heap.length - 1;
        while (i > 0) {
            const parent = (i - 1) >> 1;
            if (heap[parent] >= heap[i]) break;
            [heap[parent], heap[i]] = [heap[i], heap[parent]];
            i = parent;
        }
    }
    function pop() {  // 가장 큰 값을 꺼낸다
        const top = heap[0];
        const last = heap.pop();
        if (heap.length > 0) {
            heap[0] = last;
            let i = 0;
            while (true) {
                const l = 2 * i + 1, r = 2 * i + 2;
                let big = i;
                if (l < heap.length && heap[l] > heap[big]) big = l;
                if (r < heap.length && heap[r] > heap[big]) big = r;
                if (big === i) break;
                [heap[big], heap[i]] = [heap[i], heap[big]];
                i = big;
            }
        }
        return top;
    }
    let count = 0;  // 받은 주문 수
    let total = 0;  // 받은 주문을 쉬지 않고 모두 만들면 끝나는 시각 (최대 20억 남짓이라 수가 정확하다)
    for (const i of order) {
        count++;
        total += minutes[i];
        if (!must[i]) push(minutes[i]);
        while (total > pickup[i] && heap.length > 0) {  // 늦는다: 가장 오래 걸리는 것부터 되무른다
            total -= pop();
            count--;
        }
        if (total > pickup[i]) return [-1, -1];  // 꼭 받아야 하는 주문끼리도 지킬 수 없다
    }
    return [count, total];
}
