#include <map>
#include <string>
#include <utility>
#include <vector>

using namespace std;

vector<int> solution(int rows, int cols, vector<int> start, string commands) {
    map<char, pair<int, int>> move = {{'N', {-1, 0}}, {'S', {1, 0}}, {'W', {0, -1}}, {'E', {0, 1}}};
    int row = start[0], col = start[1];
    for (char command : commands) {
        auto [dr, dc] = move[command];
        int nextRow = row + dr, nextCol = col + dc;
        if (nextRow >= 0 && nextRow < rows && nextCol >= 0 && nextCol < cols) {
            row = nextRow;
            col = nextCol;
        }
    }
    return {row, col};
}
