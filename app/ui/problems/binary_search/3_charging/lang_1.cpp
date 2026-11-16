// 언어 함정: cpp.int_overflow @ "n은 1 이상 500,000,000 이하"
#include <string>
#include <vector>
#include <algorithm>

using namespace std;

long long solution(int n, vector<int> chargers) {
    int fastest = *min_element(chargers.begin(), chargers.end());
    // 시간은 최대 5 x 10^13이라 int를 넘는다. 시간과 개수 합은 long long으로 둔다
    long long left = 1;
    long long right = (long long)fastest * n;
    while (left < right) {
        long long mid = (left + right) / 2;
        int done = 0;
        for (int minute : chargers) {
            done += mid / minute;
        }
        if (done >= n) {
            right = mid;
        } else {
            left = mid + 1;
        }
    }
    return left;
}
