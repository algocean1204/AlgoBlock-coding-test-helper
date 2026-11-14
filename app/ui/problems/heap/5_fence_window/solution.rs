use std::cmp::Reverse;
use std::collections::BinaryHeap;

// 규칙 하나: 꼭대기를 보거나 꺼내기 전에는 언제나 이것을 부른다.
// 꼭대기에 창 밖으로 나간 판자(번호 < left)가 있으면 버린다. 힙 안쪽에 있는 것은 꼭대기에 올라올 때 버린다
// 두 힙의 원소 모양이 달라(Reverse 유무) 함수도 둘로 나눴다
fn drop_old_low(heap: &mut BinaryHeap<(i64, usize)>, left: usize) {
    while let Some(&(_, index)) = heap.peek() {
        if index < left {
            heap.pop();
        } else {
            break;
        }
    }
}

fn drop_old_high(heap: &mut BinaryHeap<Reverse<(i64, usize)>>, left: usize) {
    while let Some(&Reverse((_, index))) = heap.peek() {
        if index < left {
            heap.pop();
        } else {
            break;
        }
    }
}

fn solution(heights: Vec<i32>, w: i32) -> Vec<i64> {
    let n = heights.len();
    let w = w as usize;
    // 원소는 (높이, 번호). BinaryHeap은 기본이 최대 힙이다
    // low: 작은 쪽 절반. 그대로 쓰면 높이가 가장 큰 판자가 꼭대기에 온다. 부호를 뒤집을 필요가 없다
    let mut low: BinaryHeap<(i64, usize)> = BinaryHeap::new();
    // high: 큰 쪽 절반. Reverse로 감싸 높이가 가장 낮은 판자가 꼭대기에 오게 한다
    let mut high: BinaryHeap<Reverse<(i64, usize)>> = BinaryHeap::new();
    let mut in_low = vec![false; n]; // 판자마다 지금 low에 들어 있는지
    let mut low_count: i64 = 0;      // 창 안에 남은 판자 수. 지울 표시만 한 판자가 힙에 남아 있어 len()과 다르다
    let mut high_count: i64 = 0;
    let mut low_sum: i64 = 0;        // 합은 i32를 넘을 수 있어 i64
    let mut high_sum: i64 = 0;
    let mut left: usize = 0;         // 창의 맨 왼쪽 번호. 이보다 작은 번호는 창 밖이다
    let mut costs: Vec<i64> = Vec::new();
    for right in 0..n {
        let height = heights[right] as i64;
        // 1. 새 판자를 넣는다(4단계와 같다)
        drop_old_low(&mut low, left);
        if low.is_empty() || height <= low.peek().unwrap().0 {
            low.push((height, right));
            in_low[right] = true;
            low_count += 1;
            low_sum += height;
        } else {
            high.push(Reverse((height, right)));
            high_count += 1;
            high_sum += height;
        }
        // 2. 창이 w개를 넘으면 맨 왼쪽 판자를 뺀다. 힙에서 바로 지우지 않고 개수와 합에서만 뺀다
        if right + 1 - left > w {
            if in_low[left] {
                low_count -= 1;
                low_sum -= heights[left] as i64;
            } else {
                high_count -= 1;
                high_sum -= heights[left] as i64;
            }
            left += 1;
        }
        // 3. 개수 맞추기: low_count가 high_count와 같거나 하나 더 많게. 옮기기 전에 꼭대기의 나간 판자를 버린다
        while low_count > high_count + 1 {
            drop_old_low(&mut low, left);
            let (moved, index) = low.pop().unwrap();
            high.push(Reverse((moved, index)));
            in_low[index] = false;
            low_count -= 1;
            low_sum -= moved;
            high_count += 1;
            high_sum += moved;
        }
        while high_count > low_count {
            drop_old_high(&mut high, left);
            let Reverse((moved, index)) = high.pop().unwrap();
            low.push((moved, index));
            in_low[index] = true;
            high_count -= 1;
            high_sum -= moved;
            low_count += 1;
            low_sum += moved;
        }
        // 4. 창이 w개로 찼으면 가운데 높이(low의 꼭대기)로 맞추는 비용을 잰다
        if right + 1 - left == w {
            drop_old_low(&mut low, left);
            let middle = low.peek().unwrap().0;
            costs.push((middle * low_count - low_sum) + (high_sum - middle * high_count));
        }
    }
    costs
}
