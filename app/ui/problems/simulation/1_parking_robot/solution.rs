fn solution(rows: i32, cols: i32, start: Vec<i32>, commands: String) -> Vec<i32> {
    let mut row = start[0];
    let mut col = start[1];
    for command in commands.chars() {
        let (dr, dc) = match command {
            'N' => (-1, 0),
            'S' => (1, 0),
            'W' => (0, -1),
            _ => (0, 1),
        };
        let next_row = row + dr;
        let next_col = col + dc;
        if next_row >= 0 && next_row < rows && next_col >= 0 && next_col < cols {
            row = next_row;
            col = next_col;
        }
    }
    vec![row, col]
}
