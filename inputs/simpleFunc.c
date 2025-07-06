int add(int a, int b) {
    return a + b;
}

int add3(int a, int b, int c) {
    return a + b + c;
}

int add4(int a, int b, int c, int d) {
    return a + b + c + d;
}

int main() {
    int x = 2;
    int y = 3;
    int z = add(x, y);
    z = add3(x, y, z);
    z = add4(x, y, z, 10);
    return z;
}
