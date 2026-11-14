#include <iostream>

int main() {
    int count = 0;
    std::cin >> count;
    int total = 0;
    for (int index = 0; index < count; index += 1) {
        int value = 0;
        std::cin >> value;
        total += value;
    }
    std::cout << total << "\n";
}
