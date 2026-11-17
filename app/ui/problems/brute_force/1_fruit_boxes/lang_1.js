// 언어 함정: javascript.float_division @ "상자의 수"
function solution(apples, pears, low, high) {
    let bestSize = low;
    let bestLeft = apples + pears + 1; // 어떤 size보다도 많이 남는 값에서 시작한다
    for (let size = low; size <= high; size++) { // 상자 크기를 하나씩 대 본다
        const left = apples % size + pears % size; // 사과와 배는 섞지 않으므로 따로 남는다
        if (left <= bestLeft) { // 같을 때도 바꾸면 더 큰 size가 남는다
            bestSize = size;
            bestLeft = left;
        }
    }
    // 나눗셈 몫은 Math.floor로 정수로 맞춘다
    return [bestSize, apples / bestSize + pears / bestSize];
}
