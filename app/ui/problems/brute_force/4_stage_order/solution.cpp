#include <functional>
#include <map>
#include <string>
#include <vector>

using namespace std;

int solution(vector<string> genres) {
    // 같은 장르를 개수로 묶는다: left[장르 번호] = 아직 안 놓은 팀 수
    map<string, int> number;
    vector<int> left;
    for (const string& genre : genres) {
        if (!number.count(genre)) {
            number[genre] = left.size();
            left.push_back(0);
        }
        left[number[genre]]++;
    }

    // remaining: 더 놓아야 할 자리 수, last: 바로 앞에 놓은 장르 번호(처음에는 -1)
    function<long long(int, int)> place = [&](int remaining, int last) -> long long {
        if (remaining == 0) {
            return 1;
        }
        long long ways = 0; // 경우의 수가 int를 넘을 수 있어 long long으로 센다
        for (int genre = 0; genre < (int)left.size(); genre++) {
            if (left[genre] == 0 || genre == last) { // 놓는 도중에 가지를 끊는다
                continue;
            }
            left[genre]--;
            ways += place(remaining - 1, genre);
            left[genre]++;
        }
        return ways;
    };

    return (int)place(genres.size(), -1);
}
