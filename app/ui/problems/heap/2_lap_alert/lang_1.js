// 언어 함정: javascript.string_plus @ "MM분 SS초"
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

function solution(records, k) {
    const bigger = (a, b) => a > b; // 큰 것이 꼭대기: 최대 힙. 부호를 뒤집을 필요가 없다
    const fastest = []; // 지금까지 가장 빠른 기록 k개. 가장 느린 기록(k위)이 꼭대기에 온다
    let alerts = 0;
    for (const record of records) {
        const [minutes, seconds] = record.split(":");
        const time = minutes * 60 + seconds;
        if (fastest.length < k) {
            alerts++;
            push(fastest, time, bigger);
        } else if (time < fastest[0]) { // 지금 k위보다 빨라야 한다. 같으면 먼저 들어온 기록이 앞선다
            alerts++;
            pop(fastest, bigger);
            push(fastest, time, bigger);
        }
    }
    return alerts;
}
