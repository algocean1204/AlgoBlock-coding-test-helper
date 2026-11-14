class Solution {
    public int[] solution(int[] heights) {
        int n = heights.length;
        int[] rests = new int[n];     // rests[j]: j번 지점에서 쉬는 등산객 수
        int[] walking = new int[n];   // 아직 쉴 곳을 찾지 못한 등산객의 출발 지점(배열로 만든 스택). 위로 갈수록 높다
        int top = 0;                  // 스택에 든 개수
        for (int j = 0; j < n; j++) {
            // j번 지점이 맨 위 등산객의 출발 높이보다 낮거나 같으면, 그 등산객은 여기서 쉰다
            while (top > 0 && heights[walking[top - 1]] >= heights[j]) {
                top--;
                rests[j]++;
            }
            walking[top++] = j;  // j번 등산객이 걷기 시작한다
        }
        return rests;  // 끝까지 스택에 남은 등산객은 산책길을 벗어나 어디에도 세지 않는다
    }
}
