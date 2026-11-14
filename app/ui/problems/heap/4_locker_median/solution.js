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

function solution(houses) {
    const bigger = (a, b) => a > b;  // 큰 값이 꼭대기: 최대 힙. 부호를 뒤집을 필요가 없다
    const smaller = (a, b) => a < b; // 작은 값이 꼭대기: 최소 힙
    const low = [];  // 작은 쪽 절반
    const high = []; // 큰 쪽 절반
    let lowSum = 0;
    let highSum = 0;
    // 거리 합의 최댓값은 약 2.5e15로 2^53(약 9e15)보다 작아 Number로 충분하다. BigInt는 필요 없다
    let total = 0;
    for (const house of houses) {
        if (low.length === 0 || house <= low[0]) {
            push(low, house, bigger);
            lowSum += house;
        } else {
            push(high, house, smaller);
            highSum += house;
        }
        // 개수 맞추기: low가 high와 같거나 하나 더 많게 둔다. 그러면 low의 꼭대기가 가운데 값이다
        if (low.length > high.length + 1) {
            const moved = pop(low, bigger);
            lowSum -= moved;
            push(high, moved, smaller);
            highSum += moved;
        } else if (high.length > low.length) {
            const moved = pop(high, smaller);
            highSum -= moved;
            push(low, moved, bigger);
            lowSum += moved;
        }
        const middle = low[0];
        // (작은 쪽 집들에서 가운데까지의 거리 합) + (큰 쪽 집들에서 가운데까지의 거리 합)
        total += (middle * low.length - lowSum) + (highSum - middle * high.length);
    }
    return total;
}
