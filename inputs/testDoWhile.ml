int main() {
int i = 0;
int sum = 0;
do {
sum = sum + i;
i = i + 1;
} while (i < 5);
// sum = 0+1+2+3+4 = 10
// i = 5
return sum;
}
