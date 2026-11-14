// 자바스크립트에는 표준 힙이 없어 배열로 직접 만든다.
// less(a, b)가 참이면 a가 b보다 꼭대기에 가깝다
function push(heap, item, less) {
    heap.push(item);
    let i = heap.length - 1;
    while (i > 0) {
        const parent = (i - 1) >> 1;
        if (!less(heap[i], heap[parent])) break;
        [heap[i], heap[parent]] = [heap[parent], heap[i]];
        i = parent;
    }
}

function pop(heap, less) {
    const top = heap[0];
    const last = heap.pop();
    if (heap.length > 0) {
        heap[0] = last;
        let i = 0;
        while (true) {
            let child = 2 * i + 1;
            if (child >= heap.length) break;
            if (child + 1 < heap.length && less(heap[child + 1], heap[child])) child++;
            if (!less(heap[child], heap[i])) break;
            [heap[i], heap[child]] = [heap[child], heap[i]];
            i = child;
        }
    }
    return top;
}

// [도착 시각, 진료 시간, 위급도, 번호]: 위급도는 큰 것, 진료 시간은 짧은 것, 번호는 작은 것이 앞선다
function before(a, b) {
    if (a[2] !== b[2]) return a[2] > b[2];
    if (a[1] !== b[1]) return a[1] < b[1];
    return a[3] < b[3];
}

function solution(patients) {
    const n = patients.length;
    // 도착 시각 순으로 정렬한다. sort()는 글자 순이라 비교 함수를 준다
    const arrivals = patients.map((p, i) => [p[0], p[1], p[2], i]);
    arrivals.sort((a, b) => a[0] - b[0]);
    const waiting = []; // 도착한 동물
    let time = 0;
    let nextArrival = 0; // arrivals에서 아직 힙에 넣지 않은 첫 자리
    let total = 0;       // 합은 int를 넘지만 2^53 안이라 수 그대로 정확하다
    for (let count = 0; count < n; count++) {
        if (waiting.length === 0 && arrivals[nextArrival][0] > time) {
            time = arrivals[nextArrival][0]; // 도착한 동물이 없으면 다음 동물이 올 때까지 건너뛴다
        }
        while (nextArrival < n && arrivals[nextArrival][0] <= time) {
            push(waiting, arrivals[nextArrival], before);
            nextArrival++;
        }
        const pet = pop(waiting, before);
        total += time - pet[0];
        time += pet[1];
    }
    return total;
}
