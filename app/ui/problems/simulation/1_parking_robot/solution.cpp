#include <string>
#include <vector>

using namespace std;

vector<int> solution(int rows, int cols, vector<int> start, string commands) {
    int row = start[0], col = start[1];
    for (char command : commands) {
        int dr = 0, dc = 0;
        if (command == 'N') dr = -1;
        else if (command == 'S') dr = 1;
        else if (command == 'W') dc = -1;
        else dc = 1;
        int nextRow = row + dr, nextCol = col + dc;
        if (nextRow >= 0 && nextRow < rows && nextCol >= 0 && nextCol < cols) {
            row = nextRow;
            col = nextCol;
        }
    }
    return {row, col};
}
