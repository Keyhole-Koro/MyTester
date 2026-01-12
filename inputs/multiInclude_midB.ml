int shared_add_two(int x);
int midA(int x);

int midB(int x) {
return midA(x) + shared_add_two(x);
}
