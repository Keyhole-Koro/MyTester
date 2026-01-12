int main() {
int a = 1;
int b = 0;
int c = 1;

// (a && b) || c → (1 && 0) || 1 → 0 || 1 → 1
int x = (a && b) || c;

// a && (b || c) → 1 && (0 || 1) → 1 && 1 → 1
int y = a && (b || c);

// a || (b && c) → 1 || (0 && 1) → 1 || 0 → 1
int z = a || (b && c);

return x + y + z; // 1 + 1 + 1 = 3
}
