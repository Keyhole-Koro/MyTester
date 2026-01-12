void increment(int *ptr) {
*ptr = *ptr + 1;
}

void increment2(int **pp) {
**pp = **pp + 1;
}

int main() {
int x = 10;
increment(&x); // x becomes 11
increment(&x); // x becomes 12

int *p = &x;
increment2(&p);  // x becomes 13
increment2(&p);  // x becomes 14
return x;
}
