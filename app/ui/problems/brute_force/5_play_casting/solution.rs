// index번 배역부터 끝까지 정해서 더 얻을 수 있는 가장 큰 점수. 끝까지 정할 수 없으면 -1
fn best(index: usize, used: usize, scores: &Vec<Vec<i32>>, rival_mask: &Vec<usize>, memo: &mut Vec<Vec<i32>>) -> i32 {
    let (n, roles) = (scores.len(), scores[0].len());
    if index == roles {
        return 0;
    }
    if memo[index][used] != -2 {
        // 같은 상태에 다시 왔다: 기억한 값을 쓴다
        return memo[index][used];
    }
    let mut result = -1;
    for person in 0..n {
        if (used >> person) & 1 == 1 || scores[person][index] == 0 {
            continue;
        }
        if used & rival_mask[person] != 0 {
            // 이미 정한 단원과 부딪치면 이 가지는 버린다
            continue;
        }
        let rest = best(index + 1, used | (1 << person), scores, rival_mask, memo);
        if rest != -1 {
            // 뒤의 배역을 끝까지 정할 수 있을 때만 후보가 된다
            result = result.max(scores[person][index] + rest);
        }
    }
    memo[index][used] = result;
    result
}

fn solution(members: i32, roles: i32, auditions: Vec<Vec<i32>>, rivals: Vec<Vec<i32>>) -> i32 {
    let (n, roles) = (members as usize, roles as usize);
    let mut scores = vec![vec![0; roles]; n]; // scores[단원][배역] = 오디션 점수. 0은 오디션을 보지 않아 맡을 수 없다는 뜻
    for a in &auditions {
        scores[a[0] as usize][a[1] as usize] = a[2];
    }
    let mut rival_mask = vec![0usize; n]; // 함께 무대에 설 수 없는 단원들(비트, 양쪽에 모두 적는다)
    for pair in &rivals {
        let (a, b) = (pair[0] as usize, pair[1] as usize);
        rival_mask[a] |= 1 << b;
        rival_mask[b] |= 1 << a;
    }
    // memo[몇 번 배역부터][누구를 썼는가(비트)] = 거기서 더 얻을 수 있는 가장 큰 점수. -2는 아직 모름
    let mut memo = vec![vec![-2; 1 << n]; roles];
    best(0, 0, &scores, &rival_mask, &mut memo)
}
