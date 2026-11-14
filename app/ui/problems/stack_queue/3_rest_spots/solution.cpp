#include <vector>

using namespace std;

vector<int> solution(vector<int> heights) {
    int n = heights.size();
    vector<int> rests(n, 0);  // rests[j]: j번 지점에서 쉬는 등산객 수
    vector<int> walking;      // 아직 쉴 곳을 찾지 못한 등산객의 출발 지점. 위로 갈수록 높다
    for (int j = 0; j < n; j++) {
        // j번 지점이 맨 위 등산객의 출발 높이보다 낮거나 같으면, 그 등산객은 여기서 쉰다
        while (!walking.empty() && heights[walking.back()] >= heights[j]) {
            walking.pop_back();
            rests[j]++;
        }
        walking.push_back(j);  // j번 등산객이 걷기 시작한다
    }
    return rests;  // 끝까지 스택에 남은 등산객은 산책길을 벗어나 어디에도 세지 않는다
}
