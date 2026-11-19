class Solution {
    public int solution(int[][] rails) {
        int n = rails.length;
        boolean[] onRoute = new boolean[n]; // 지금 만들고 있는 길 위에 있는 역

        class Routes {
            // station까지 왔을 때, 여기서 n - 1번 역까지 이어 갈 수 있는 길의 수
            int countFrom(int station) {
                if (station == n - 1) return 1; // 도착: 길 하나가 완성되고 여기서 끝난다
                int routes = 0;
                for (int next = 0; next < n; next++) {
                    if (rails[station][next] == 1 && !onRoute[next]) {
                        onRoute[next] = true; // 들어갈 때 표시한다
                        routes += countFrom(next);
                        onRoute[next] = false; // 돌아올 때 지운다: 다른 갈래에서 이 역을 다시 쓸 수 있게
                    }
                }
                return routes;
            }
        }

        onRoute[0] = true; // 출발역도 길 위에 있다
        return new Routes().countFrom(0);
    }
}
