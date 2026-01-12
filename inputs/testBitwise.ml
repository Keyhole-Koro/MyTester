int main() {
int a = 12; // 1100
int b = 10; // 1010
int c = a & b; // 1000 = 8
int d = a | b; // 1110 = 14
int e = a ^ b; // 0110 = 6
int g = !a;    // 0
int h = !0;    // 1

// c=8, d=14, e=6, g=0, h=1
// Sum = 29
return c + d + e + g + h;
}
