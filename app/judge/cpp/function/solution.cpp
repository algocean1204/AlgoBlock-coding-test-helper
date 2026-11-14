#include <numeric>
#include <vector>

int solution(std::vector<int> numbers) {
    return std::accumulate(numbers.begin(), numbers.end(), 0);
}
