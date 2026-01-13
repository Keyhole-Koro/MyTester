int main() {
    int x = 2;
    int var = case x of {
        0 -> 10;
        1 -> 20;
        2 -> 30;
        _ -> -1;
    };
    return var;
}
