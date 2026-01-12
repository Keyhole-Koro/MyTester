int main() {
int i = 0;
int sum = 0;

while (i < 10) {
i++;

if (i % 2 == 0) continue;  // Skip even numbers

if (i == 9) break;         // Stop before reaching 9

sum = sum + i;
}

return sum;  // i=1→sum=1, i=3→sum=4, i=5→sum=9, i=7→sum=16 → return 16
}
