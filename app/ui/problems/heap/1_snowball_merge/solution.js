// 자바스크립트에는 표준 힙이 없어 배열로 직접 만든다.
// less(a, b)가 참이면 a가 b보다 꼭대기에 가깝다(최소 힙이면 a < b)
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

function solution(snowballs) {
    const smaller = (a, b) => a < b;
    const heap = [];
    for (const snowball of snowballs) push(heap, snowball, smaller);
    let total = 0; // 최대 약 4e10이라 Number(2^53까지 정확)로 충분하다
    while (heap.length > 1) {
        const lightest = pop(heap, smaller);
        const second = pop(heap, smaller);
        const merged = lightest + second;
        total += merged;
        push(heap, merged, smaller);
    }
    return total;
}
