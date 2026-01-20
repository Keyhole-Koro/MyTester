int main() {
    int outer = (int a) {
        int inner = (int b) {
            return b + 1;
        };
        return inner(a) + 2;
    };

    return outer(3);
}
