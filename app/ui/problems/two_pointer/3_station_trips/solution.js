function solution(gaps, k) {
    let count = 0;
    let left = 0;
    let total = 0; // gaps[left]부터 gaps[right]까지의 합 = left번 역에서 right + 1번 역까지의 거리
    for (let right = 0; right < gaps.length; right++) {
        total += gaps[right];
        // 거리가 모두 양수라 왼쪽을 당기면 합이 줄어든다. k 이하가 될 때까지 당긴다
        while (total > k) {
            total -= gaps[left];
            left++;
        }
        if (total === k) {
            count++;
        }
    }
    return count;
}
