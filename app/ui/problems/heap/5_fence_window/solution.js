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

// 원소는 [높이, 번호]
// low: 높이가 큰 판자가 꼭대기에 온다(부호를 뒤집는 대신 비교 방향을 바꾼다)
const lowFirst = (a, b) => (a[0] !== b[0] ? a[0] > b[0] : a[1] < b[1]);
// high: 높이가 낮은 판자가 꼭대기에 온다
const highFirst = (a, b) => (a[0] !== b[0] ? a[0] < b[0] : a[1] < b[1]);

// 규칙 하나: 꼭대기를 보거나 꺼내기 전에는 언제나 이것을 부른다.
// 꼭대기에 창 밖으로 나간 판자(번호 < left)가 있으면 버린다. 힙 안쪽에 있는 것은 꼭대기에 올라올 때 버린다
function dropOld(heap, left, less) {
    while (heap.length > 0 && heap[0][1] < left) {
        pop(heap, less);
    }
}

function solution(heights, w) {
    const n = heights.length;
    const low = [];  // 작은 쪽 절반
    const high = []; // 큰 쪽 절반
    const inLow = new Array(n).fill(false); // 판자마다 지금 low에 들어 있는지
    let lowCount = 0;  // 창 안에 남은 판자 수. 지울 표시만 한 판자가 힙에 남아 있어 length와 다르다
    let highCount = 0;
    // 합과 비용의 최댓값은 약 1e14로 2^53(약 9e15)보다 작아 Number로 충분하다
    let lowSum = 0;
    let highSum = 0;
    let left = 0;      // 창의 맨 왼쪽 번호. 이보다 작은 번호는 창 밖이다
    const costs = [];
    for (let right = 0; right < n; right++) {
        const height = heights[right];
        // 1. 새 판자를 넣는다(4단계와 같다)
        dropOld(low, left, lowFirst);
        if (low.length === 0 || height <= low[0][0]) {
            push(low, [height, right], lowFirst);
            inLow[right] = true;
            lowCount++;
            lowSum += height;
        } else {
            push(high, [height, right], highFirst);
            highCount++;
            highSum += height;
        }
        // 2. 창이 w개를 넘으면 맨 왼쪽 판자를 뺀다. 힙에서 바로 지우지 않고 개수와 합에서만 뺀다
        if (right - left + 1 > w) {
            if (inLow[left]) {
                lowCount--;
                lowSum -= heights[left];
            } else {
                highCount--;
                highSum -= heights[left];
            }
            left++;
        }
        // 3. 개수 맞추기: lowCount가 highCount와 같거나 하나 더 많게. 옮기기 전에 꼭대기의 나간 판자를 버린다
        while (lowCount > highCount + 1) {
            dropOld(low, left, lowFirst);
            const moved = pop(low, lowFirst);
            push(high, moved, highFirst);
            inLow[moved[1]] = false;
            lowCount--;
            lowSum -= moved[0];
            highCount++;
            highSum += moved[0];
        }
        while (highCount > lowCount) {
            dropOld(high, left, highFirst);
            const moved = pop(high, highFirst);
            push(low, moved, lowFirst);
            inLow[moved[1]] = true;
            highCount--;
            highSum -= moved[0];
            lowCount++;
            lowSum += moved[0];
        }
        // 4. 창이 w개로 찼으면 가운데 높이(low의 꼭대기)로 맞추는 비용을 잰다
        if (right - left + 1 === w) {
            dropOld(low, left, lowFirst);
            const middle = low[0][0];
            costs.push((middle * lowCount - lowSum) + (highSum - middle * highCount));
        }
    }
    return costs;
}
