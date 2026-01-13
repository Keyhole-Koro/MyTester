int main() {
    int var = ({
        int a = 2;
        int b = ({
            int c = 1;
            int d = 2;
            yield c + d;
        });
        yield a + b;
    });
    return var;
}