#include <map>
#include <string>
#include <utility>
#include <vector>

using namespace std;

long long solution(vector<string> board) {
    int rows = board.size(), cols = board[0].size();
    map<char, pair<int, int>> step = {{'U', {-1, 0}}, {'D', {1, 0}}, {'L', {0, -1}}, {'R', {0, 1}}};
    const int NEW = 0, ON_PATH = 1, DONE = 2; // 아직 안 감 / 지금 걷는 길 위 / 점수가 정해짐
    vector<vector<int>> state(rows, vector<int>(cols, NEW));
    vector<vector<int>> order(rows, vector<int>(cols, 0)); // 지금 길에서 몇 번째로 밟은 칸인가
    vector<vector<int>> score(rows, vector<int>(cols, 0));
    for (int startR = 0; startR < rows; startR++) {
        for (int startC = 0; startC < cols; startC++) {
            if (state[startR][startC] == DONE) continue;
            // 1. 밖으로 나가거나, 점수가 정해진 칸에 닿거나, 지금 길 위의 칸에 다시 닿을 때까지 걸으며 길을 적는다
            vector<int> path; // 칸 번호 = 행 * cols + 열
            int r = startR, c = startC;
            int nextScore;
            while (true) {
                state[r][c] = ON_PATH;
                order[r][c] = path.size();
                path.push_back(r * cols + c);
                auto [dr, dc] = step[board[r][c]];
                r += dr;
                c += dc;
                if (r < 0 || r >= rows || c < 0 || c >= cols) {
                    nextScore = 0; // 밖이다: 더 밟을 칸이 없다
                    break;
                }
                if (state[r][c] == DONE) {
                    nextScore = score[r][c]; // 답을 아는 칸: 더 걷지 않고 이어 쓴다
                    break;
                }
                if (state[r][c] == ON_PATH) {
                    // 고리: 다시 닿은 칸부터 지금 칸까지. 고리 위의 칸은 어디서 출발하든 고리를 한 바퀴 돈다
                    int first = order[r][c];
                    int length = path.size() - first;
                    for (size_t i = first; i < path.size(); i++) {
                        score[path[i] / cols][path[i] % cols] = length;
                        state[path[i] / cols][path[i] % cols] = DONE;
                    }
                    path.resize(first); // 남은 것은 고리로 들어가기 전의 칸들
                    nextScore = length;
                    break;
                }
            }
            // 2. 걸어온 길을 거꾸로 돌아오며 '다음 칸의 점수 + 1'을 적는다
            for (int i = (int)path.size() - 1; i >= 0; i--) {
                nextScore++;
                score[path[i] / cols][path[i] % cols] = nextScore;
                state[path[i] / cols][path[i] % cols] = DONE;
            }
        }
    }
    long long total = 0; // 합은 최대 약 6백억이라 long long이 필요하다
    for (auto& row : score) for (int s : row) total += s;
    return total;
}
