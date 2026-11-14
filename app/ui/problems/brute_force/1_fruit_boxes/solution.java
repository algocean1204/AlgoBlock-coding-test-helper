class Solution {
    public int[] solution(int apples, int pears, int low, int high) {
        int bestSize = low;
        int bestLeft = apples + pears + 1; // 어떤 size보다도 많이 남는 값에서 시작한다
        for (int size = low; size <= high; size++) { // 상자 크기를 하나씩 대 본다
            int left = apples % size + pears % size; // 사과와 배는 섞지 않으므로 따로 남는다
            if (left <= bestLeft) { // 같을 때도 바꾸면 더 큰 size가 남는다
                bestSize = size;
                bestLeft = left;
            }
        }
        return new int[]{bestSize, apples / bestSize + pears / bestSize};
    }
}
