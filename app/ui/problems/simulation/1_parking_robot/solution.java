import java.util.Map;

class Solution {
    public int[] solution(int rows, int cols, int[] start, String commands) {
        Map<Character, int[]> move = Map.of('N', new int[]{-1, 0}, 'S', new int[]{1, 0}, 'W', new int[]{0, -1}, 'E', new int[]{0, 1});
        int row = start[0], col = start[1];
        for (char command : commands.toCharArray()) {
            int[] d = move.get(command);
            int nextRow = row + d[0], nextCol = col + d[1];
            if (nextRow >= 0 && nextRow < rows && nextCol >= 0 && nextCol < cols) {
                row = nextRow;
                col = nextCol;
            }
        }
        return new int[]{row, col};
    }
}
