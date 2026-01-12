import { inc_one } from "multiInclude_part1.ml";
import { add_pair } from "multiInclude_part2.ml";

int main() {
int base = 4;
int first = inc_one(base);
int total = add_pair(first, 6);
return total;
}
