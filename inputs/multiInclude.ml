package main;
import part1;
import part2;

int main() {
    int base = 4;
    int first = part1.inc_one(base);
    int total = part2.add_pair(first, 6);
    return total;
}
