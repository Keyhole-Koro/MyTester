int test_eq(int a, int b) {
int r = 0;
if (a == b) {
r = 10;
} else {
r = 11;
}
return r;
}

int test_neq(int a, int b) {
int r = 0;
if (a != b) {
r = 20;
} else {
r = 21;
}
return r;
}

int test_lt(int a, int b) {
int r = 0;
if (a < b) {
r = 30;
} else {
r = 31;
}
return r;
}

int test_lte(int a, int b) {
int r = 0;
if (a <= b) {
r = 40;
} else {
r = 41;
}
return r;
}

int test_gt(int a, int b) {
int r = 0;
if (a > b) {
r = 50;
} else {
r = 51;
}
return r;
}

int test_gte(int a, int b) {
int r = 0;
if (a >= b) {
r = 60;
} else {
r = 61;
}
return r;
}

int add4(int a, int b, int c, int d) {
return a + b + c + d;
}

int main() {
int x = 2;
int y = 3;

int eq  = test_eq(x, y);    // 11

int neq = test_neq(x, y);   // 20
int lt  = test_lt(x, y);    // 30
int lte = test_lte(x, y);   // 40
int gt  = test_gt(x, y);    // 51
int gte = test_gte(x, y);   // 61

if (x > 9) {
x = x + 1; // x becomes 3 (not taken)
}

int z = add4(x, y, 10, 100); // 2+3+10+100=115

// Optional: add all the results so the output is unique and you can verify!
return eq+
neq +
lt +
lte +
gt +
gte +
z; // 11 + 20 + 30 + 40 + 51 + 61 + 115 = 328
// Should be: 11+20+30+40+51+61+15 = 228

}
