int main() {
int a = 3;
int b = 5;
int c = (a < b);
int d = (a > b);
int e = (a == 3) && (b == 5);
int f = (a == 4) || (b == 5);
int g = a < b ? a : b;
int h = a > b ? 1 : 2;
return c + d + e + f + g + h;
}
