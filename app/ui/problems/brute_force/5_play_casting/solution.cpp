#include <vector>
#include <algorithm>

using namespace std;

static int n, roleTotal;
static vector<vector<int>> score;
static vector<int> rivalMask;  // rivalMask[i]: i번 단원과 함께 무대에 설 수 없는 단원들(비트, 양쪽에 모두 적는다)
static vector<vector<int>> memo;  // memo[몇 번 배역부터][누구를 썼는가(비트)] = 거기서 더 얻을 수 있는 가장 큰 점수. -2는 아직 모름

// index번 배역부터 끝까지 정해서 더 얻을 수 있는 가장 큰 점수. 끝까지 정할 수 없으면 -1
int best(int index, int used) {
    if (index == roleTotal) {
        return 0;
    }
    if (memo[index][used] != -2) {  // 같은 상태에 다시 왔다: 기억한 값을 쓴다
        return memo[index][used];
    }
    int result = -1;
    for (int person = 0; person < n; person++) {
        if ((used >> person & 1) == 1 || score[person][index] == 0) {
            continue;
        }
        if ((used & rivalMask[person]) != 0) {  // 이미 정한 단원과 부딪치면 이 가지는 버린다
            continue;
        }
        int rest = best(index + 1, used | 1 << person);
        if (rest != -1) {  // 뒤의 배역을 끝까지 정할 수 있을 때만 후보가 된다
            result = max(result, score[person][index] + rest);
        }
    }
    memo[index][used] = result;
    return result;
}

int solution(int members, int roles, vector<vector<int>> auditions, vector<vector<int>> rivals) {
    n = members;
    roleTotal = roles;
    score.assign(n, vector<int>(roleTotal, 0));  // score[단원][배역] = 오디션 점수. 0은 오디션을 보지 않아 맡을 수 없다는 뜻
    for (const auto& a : auditions) {
        score[a[0]][a[1]] = a[2];
    }
    rivalMask.assign(n, 0);
    for (const auto& pair : rivals) {
        rivalMask[pair[0]] |= 1 << pair[1];
        rivalMask[pair[1]] |= 1 << pair[0];
    }
    memo.assign(roleTotal, vector<int>(1 << n, -2));
    return best(0, 0);
}
