class Solution {
    public int[] solution(int rows, int cols, int[] start, String commands) {
        int row = start[0], col = start[1];
        for (int i = 0; i < commands.length(); i++) {
            char command = commands.charAt(i);
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
        return new int[]{row, col};
    }
}
