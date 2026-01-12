int main() {
int x = 2;
int y = 3;

for (int i = 0; i < 20; i++) {
x++;
if (x > 10)
break;
} // 11

for (int i = 10; i > 0; i--) {
if (i == 6)
continue;
y--;
} // -6

return x + y;
}
