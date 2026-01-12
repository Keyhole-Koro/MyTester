int fib(int n) {
if (n <= 1) return n;
return fib(n-1) + fib(n-2);
}

int factorial(int n) {
if (n == 0) return 1;
return n * factorial(n - 1);
}

int main() {
int sum = 0;
int i;

// Test for loop and recursion (fib)
for (i = 0; i < 10; i++) {
if (i % 2 == 0) {
sum = sum + i;
} else {
sum = sum + fib(i);
}
}

// Test logic and simple if
int x = 10;
int y = 20;
int z = 0;
if (x < y && y > 15) {
z = 1;
} else {
z = 0;
}

// Test while loop
int count = 0;
while (count < 5) {
sum = sum + 1;
count++;
}

// Test another recursion (factorial)
int f = factorial(5); // 120
if (f == 120) {
z = z + 1; // z becomes 2 if logic passed
}

// arithmetic complexity
int complex_math = (x * y + f) / (z + 1);

return sum + z + complex_math;
}
