use std::io::{self, BufRead};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    let count: usize = lines.next().unwrap().unwrap().parse().unwrap();
    let mut total = 0;
    for _ in 0..count {
        total += lines.next().unwrap().unwrap().parse::<i32>().unwrap();
    }
    println!("{total}");
}
